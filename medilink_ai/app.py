"""FastAPI service. Identity here is a header stub; in production authenticate with Medilink SSO/JWT."""
from __future__ import annotations
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
import json
from pathlib import Path
from tempfile import NamedTemporaryFile

from . import analytics
from .audit import AuditLog
from .authz import Authorizer, User
from .config import Settings
from .context import ContextBuilder
from .demo_data import HMIS, USERS
from .gateway import Gateway
from .llm import MockLLM, OllamaLLM, OpenAICompatLLM
from .rag import KnowledgeIndex
from .backend import BackendAccessError, BackendHMISReader, MedilinkBackend
from .rate_limit import RateLimiter
from .registry import platform_registry
from .knowledge.ingestion import ingest_document
from .knowledge.schemas import DocumentMetadataRequest, IngestionResponse
from .knowledge.access import KnowledgeAccessContext
from .knowledge.retrieval import retrieve
from .knowledge.retrieval_schemas import KnowledgeSearchRequest, KnowledgeSearchResponse, KnowledgeSource
from .db.session import get_db
from .knowledge.hybrid_schemas import HybridSearchRequest, HybridSearchResponse, HybridSearchSource
from .knowledge.retrieval_pipeline import KnowledgeRetrievalPipeline
from .knowledge.assistant_service import HospitalKnowledgeAssistant
from .knowledge.assistant_schemas import KnowledgeAssistantRequest, KnowledgeAssistantResponse
from .gateway.api import router as ai_gateway_router
from .gateway.identity import create_identity_provider


class NoteReq(BaseModel):
    patient_id: str
    transcript: str

class QReq(BaseModel):
    question: str

class ActionReq(BaseModel):
    request_id: str
    action: str
    final_text: str | None = None

class DupReq(BaseModel):
    candidate: dict
    existing: list

class QueueReq(BaseModel):
    queue_length: int
    servers: int
    avg_service_min: float
    target_min: float

class LeakReq(BaseModel):
    services: list
    charges: list

class FeedbackReq(BaseModel):
    comments: list


def create_app(settings: Settings | None = None, llm=None, hmis=None) -> FastAPI:
    s = settings or Settings()
    if llm is None:
        if s.use_mock_llm:
            llm = MockLLM()
        elif s.llm_protocol == "ollama":
            llm = OllamaLLM(
                s.llm_base_url,
                s.llm_model,
                s.allowed_hosts,
                s.request_timeout_s,
                s.ollama_keep_alive,
                s.ollama_num_ctx,
                s.ollama_num_predict,
                s.ollama_num_thread,
            )
        elif s.llm_protocol in {"openai", "openai-compatible", "openai_compatible"}:
            llm = OpenAICompatLLM(s.llm_base_url, s.llm_model, s.allowed_hosts, s.request_timeout_s)
        else:
            raise ValueError("MEDILINK_LLM_PROTOCOL must be 'ollama' or 'openai-compatible'.")
    kb = KnowledgeIndex()
    kb.load_dir(s.knowledge_dir)
    kb.load_store(str(s.resolved_knowledge_store()))
    authz, audit = Authorizer(), AuditLog(s.audit_db)
    demo_hmis = hmis or HMIS
    backend = MedilinkBackend(s.backend_base_url, s.backend_allowed_hosts, s.backend_timeout_s) if s.auth_mode == "medilink" else None
    limiter = RateLimiter(s.request_rate_per_minute)
    gw = Gateway(s, llm, authz, ContextBuilder(demo_hmis), audit, kb)
    app = FastAPI(title="Medilink AI Gateway", version="0.1.0")
    # The gateway consumes a principal established by trusted Medilink
    # middleware. It never authenticates browser headers or request-body claims.
    app.state.identity_provider = create_identity_provider()
    app.include_router(ai_gateway_router)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(s.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )

    def current_user(
        authorization: str | None = Header(default=None),
        x_user_id: str | None = Header(default=None),
    ) -> tuple[User, str | None]:
        if s.auth_mode == "medilink":
            if not authorization or not authorization.lower().startswith("bearer "):
                raise HTTPException(401, "Bearer token required.")
            token = authorization.split(" ", 1)[1].strip()
            try:
                user = backend.resolve_user(token) if backend else None
            except BackendAccessError as exc:
                raise HTTPException(401, str(exc)) from exc
            if not user or not user.id:
                raise HTTPException(401, "Medilink identity could not be resolved.")
            if not limiter.allow(user.id):
                raise HTTPException(429, "AI request rate limit reached. Please retry shortly.")
            return user, token
        if not x_user_id or x_user_id not in USERS:
            raise HTTPException(401, "unknown user")
        if not limiter.allow(x_user_id):
            raise HTTPException(429, "AI request rate limit reached. Please retry shortly.")
        return USERS[x_user_id], None

    def request_gateway(identity: tuple[User, str | None]) -> tuple[Gateway, User]:
        user, token = identity
        if token and backend:
            return Gateway(s, llm, authz, ContextBuilder(BackendHMISReader(backend, token)), audit, kb), user
        return gw, user

    @app.get("/v1/summary/{patient_id}")
    def summary(patient_id: str, identity=Depends(current_user)):
        gateway, u = request_gateway(identity)
        try:
            return gateway.summarize_patient(u, patient_id).dict()
        except (KeyError, BackendAccessError):
            raise HTTPException(404, "Patient record is unavailable to this user.")

    @app.post("/v1/note-draft")
    def note(req: NoteReq, identity=Depends(current_user)):
        if len(req.transcript) > s.max_transcript_chars:
            raise HTTPException(413, "Dictation exceeds the configured size limit.")
        gateway, u = request_gateway(identity)
        # A draft contains patient-linked clinical information. In production,
        # perform an authorised read first instead of trusting only an ID sent by
        # the browser.
        token = identity[1]
        if token and backend:
            try:
                backend.patient_record(req.patient_id, token)
            except BackendAccessError as exc:
                raise HTTPException(403, str(exc)) from exc
        return gateway.draft_note(u, req.patient_id, req.transcript).dict()

    @app.post("/v1/knowledge")
    def knowledge(req: QReq, identity=Depends(current_user)):
        if len(req.question) > 4000:
            raise HTTPException(413, "Question exceeds the configured size limit.")
        gateway, u = request_gateway(identity)
        return gateway.ask_knowledge(u, req.question).dict()

    @app.post("/v1/knowledge/ingest", response_model=IngestionResponse)
    async def ingest_knowledge_document(
        metadata: str = Form(...),
        document: UploadFile = File(...),
        identity=Depends(current_user),
    ):
        user, _ = identity
        admin_roles = {"super_admin", "hospital_admin", "admin", "administrator", "facility_admin", "tenant_admin"}
        if user.role.lower() not in admin_roles:
            raise HTTPException(403, "Only facility administrators can ingest knowledge documents.")
        filename = Path(document.filename or "").name
        if not filename or Path(filename).suffix.lower() not in {".txt", ".md", ".pdf"}:
            raise HTTPException(415, "Only TXT, Markdown and PDF documents are supported.")
        try:
            request = DocumentMetadataRequest.model_validate(json.loads(metadata))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise HTTPException(422, "Invalid document metadata.") from exc
        if user.facility_id and (request.facility_id != user.facility_id or request.organization_id != user.facility_id):
            raise HTTPException(403, "Document organization and facility must match the signed-in facility.")
        if request.classification == "RESTRICTED" and not user.role.lower() in {"super_admin", "hospital_admin", "facility_admin"}:
            raise HTTPException(403, "Restricted documents require an administrator.")
        contents = await document.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(413, "Knowledge documents must be 10 MB or smaller.")
        temporary_path = None
        try:
            with NamedTemporaryFile(prefix="medilink-knowledge-", suffix=Path(filename).suffix, delete=False) as handle:
                handle.write(contents)
                temporary_path = Path(handle.name)
            doc_id, characters, chunks = ingest_document(
                temporary_path, request, s.resolved_knowledge_store(), source_filename=filename
            )
            # Reload the index atomically so a newly ingested document is
            # searchable immediately and is not duplicated in memory.
            kb.chunks.clear()
            kb.load_dir(s.knowledge_dir)
            kb.load_store(str(s.resolved_knowledge_store()))
            audit.write(audit.new_request_id(), "AI_KNOWLEDGE_INGESTED", user.id, None, {"document_id": doc_id, "filename": filename, "chunks": chunks})
            return IngestionResponse(status="success", document_id=doc_id, title=request.title, source_filename=filename, extracted_characters=characters, chunk_count=chunks, message="Document successfully ingested into the local knowledge store.")
        except (ValueError, FileNotFoundError) as exc:
            raise HTTPException(422, str(exc)) from exc
        finally:
            if temporary_path:
                temporary_path.unlink(missing_ok=True)

    @app.post("/v1/knowledge/search", response_model=KnowledgeSearchResponse)
    def search_knowledge(request: KnowledgeSearchRequest, identity=Depends(current_user)):
        user, _ = identity
        context = KnowledgeAccessContext(
            user_id=user.id,
            organization_id=user.facility_id or "",
            facility_id=user.facility_id or "",
            department_id=None,
            roles=frozenset({user.role}),
            classification_level="INTERNAL",
        )
        try:
            results = retrieve(request.query, context, s.resolved_knowledge_store(), request.top_k)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        return KnowledgeSearchResponse(
            status="success",
            query=request.query,
            results=[KnowledgeSource(
                chunk_id=result.chunk.chunk_id,
                document_id=result.chunk.document_id,
                title=result.chunk.metadata.title,
                version=result.chunk.metadata.version,
                source_filename=result.chunk.metadata.source_filename,
                chunk_index=result.chunk.chunk_index,
                score=round(result.score, 4),
            ) for result in results],
        )

    @app.post("/v1/knowledge/hybrid-search", response_model=HybridSearchResponse)
    def hybrid_search(
        request: HybridSearchRequest,
        identity=Depends(current_user),
        db: Session = Depends(get_db),
    ):
        """Return authorized lexical and semantic knowledge matches."""
        user, _ = identity
        context = KnowledgeAccessContext(
            user_id=user.id,
            organization_id=user.facility_id or "",
            facility_id=user.facility_id or "",
            department_id=None,
            roles=frozenset({user.role}),
            classification_level="INTERNAL",
        )
        try:
            results = KnowledgeRetrievalPipeline(db).search(
                request.query,
                context=context,
                top_k=request.top_k,
                candidate_limit=min(50, max(request.top_k * 5, 20)),
            ).candidates
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        except (SQLAlchemyError, RuntimeError) as exc:
            raise HTTPException(503, "Hybrid knowledge search is temporarily unavailable.") from exc
        return HybridSearchResponse(
            status="success",
            query=request.query,
            results=[
                HybridSearchSource(
                    chunk_id=result.chunk_id,
                    document_id=str(result.chunk.document.id),
                    title=result.chunk.document.title,
                    version=result.chunk.document.version,
                    source_filename=result.chunk.document.source_filename,
                    chunk_index=result.chunk.chunk_index,
                    hybrid_score=round(result.score, 6),
                    keyword_rank=result.keyword_rank,
                    vector_rank=result.vector_rank,
                )
                for result in results
            ],
        )

    @app.post("/v1/knowledge/ask", response_model=KnowledgeAssistantResponse)
    async def ask_hospital_knowledge(
        request: KnowledgeAssistantRequest,
        identity=Depends(current_user),
        db: Session = Depends(get_db),
    ):
        """Generate a structured, cited answer from authorized evidence."""
        user, _ = identity
        context = KnowledgeAccessContext(
            user_id=user.id,
            organization_id=user.facility_id or "",
            facility_id=user.facility_id or "",
            department_id=None,
            roles=frozenset({user.role}),
            classification_level="INTERNAL",
        )
        try:
            answer = await HospitalKnowledgeAssistant(db).ask(request.query, context)
        except (SQLAlchemyError, RuntimeError) as exc:
            raise HTTPException(503, "Grounded knowledge generation is temporarily unavailable.") from exc
        return KnowledgeAssistantResponse(**answer.model_dump())

    @app.post("/v1/human-action")
    def human(req: ActionReq, identity=Depends(current_user)):
        gateway, u = request_gateway(identity)
        return gateway.record_human_action(u, req.request_id, req.action, req.final_text)

    def need(u: User, perm: str):
        if not authz.can(u, perm):
            raise HTTPException(403, "access denied")

    @app.post("/v1/duplicates")
    def dups(req: DupReq, identity=Depends(current_user)):
        _, u = request_gateway(identity)
        need(u, "ai.duplicates")
        result = analytics.find_duplicates(req.candidate, req.existing)
        audit.write(audit.new_request_id(), "AI_ANALYTICS", u.id, None, {"capability": "duplicates", "matches": len(result)})
        return result

    @app.post("/v1/queue-forecast")
    def queue(req: QueueReq, identity=Depends(current_user)):
        _, u = request_gateway(identity)
        need(u, "ai.queue")
        result = analytics.queue_forecast(req.queue_length, req.servers, req.avg_service_min, req.target_min)
        audit.write(audit.new_request_id(), "AI_ANALYTICS", u.id, None, {"capability": "queue_forecast"})
        return result

    @app.post("/v1/revenue-leakage")
    def leak(req: LeakReq, identity=Depends(current_user)):
        _, u = request_gateway(identity)
        need(u, "ai.revenue")
        result = analytics.revenue_leakage(req.services, req.charges)
        audit.write(audit.new_request_id(), "AI_ANALYTICS", u.id, None, {"capability": "revenue_leakage"})
        return result

    @app.post("/v1/feedback-themes")
    def feedback(req: FeedbackReq, identity=Depends(current_user)):
        _, u = request_gateway(identity)
        need(u, "ai.feedback")
        result = analytics.feedback_themes(req.comments)
        audit.write(audit.new_request_id(), "AI_ANALYTICS", u.id, None, {"capability": "feedback_themes", "comments": len(req.comments)})
        return result

    @app.get("/v1/audit/verify")
    def verify(identity=Depends(current_user)):
        _, u = request_gateway(identity)
        if not authz.can(u, "ai.knowledge"):
            raise HTTPException(403, "access denied")
        return {"chain_intact": audit.verify_chain()}

    @app.get("/healthz")
    def health():
        return {"status": "ok", "mode": s.auth_mode, "model": llm.name, "audit_chain_intact": audit.verify_chain()}

    @app.get("/v1/platform")
    def platform(identity=Depends(current_user)):
        _, user = request_gateway(identity)
        return {
            **platform_registry(),
            "service": {"mode": s.auth_mode, "model": llm.name, "audit_chain_intact": audit.verify_chain()},
            "user": {"role": user.role, "facilityId": user.facility_id},
        }

    @app.get("/v1/patients/search")
    def patient_search(q: str = "", identity=Depends(current_user)):
        _, user = request_gateway(identity)
        token = identity[1]
        if not token or not backend:
            raise HTTPException(503, "Patient search requires Medilink production identity mode.")
        try:
            matches = backend.search_patients(q, token)
        except BackendAccessError as exc:
            raise HTTPException(403, str(exc)) from exc
        audit.write(audit.new_request_id(), "AI_PATIENT_SEARCH", user.id, None, {"query_length": len(q), "matches": len(matches)})
        return {"items": matches}

    return app
