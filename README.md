# Medilink AI Platform (Phase 2 retrieval)

Private, hospital-hosted, advisory-only AI for Medilink HMIS. No external AI API is ever called.

## What is built
| Piece | File | Rule it enforces |
|---|---|---|
| AI Gateway | `gateway.py` | authz -> safety -> context -> model -> validation -> audit, for every request |
| Local inference client | `llm.py` | refuses any endpoint that is not loopback / private IP / allow-listed host |
| Authorization adapter | `authz.py` | AI inherits Medilink permissions + care-team check; no own DB account |
| Context builder | `context.py` | purpose-limited, identifiers stripped, every fact numbered `[S#]` with a source record ref |
| Safety engine | `safety.py` | refuses command-style requests; blocks uncited, fake-cited or directive/diagnostic output |
| Audit trail | `audit.py` | AI_REQUEST / AI_OUTPUT / HUMAN_ACTION, hash-chained, tamper-evident |
| Knowledge assistant | `rag.py` | answers only from approved docs, cites doc + version, says "not found" otherwise |
| Phase 1 analytics | `analytics.py` | duplicate patients, queue forecast, revenue leakage, discount outliers, feedback themes |
| Medilink identity bridge | `backend.py` | forwards the caller's Medilink bearer token; no AI service account or database credentials |
| Backend reader | `backend.py` | read-only, purpose-limited patient context through the existing patient API |
| Operational controls | `rate_limit.py`, `app.py` | per-user request cap, transcript size cap, health endpoint and audit events for analytics |
| AI contracts and router | `contracts.py`, `router.py` | standard task, priority and route decisions; deterministic work is never sent to an LLM |
| Knowledge access filter | `rag.py` | optional document `allowed_roles` and `facility_id` metadata are enforced before retrieval |
| Hybrid retrieval | `rag.py`, `knowledge/embeddings.py` | BM25-style keyword ranking plus deterministic local semantic similarity; no external embedding calls |
| Evidence contract | `knowledge/grounding.py`, `knowledge/retrieval.py` | authorized chunks carry document/version/source metadata and are supplied as evidence, never executable instructions |
| PostgreSQL/pgvector schema | `sql/001_knowledge_pgvector.sql` | isolated document/chunk tables with vector(256) and HNSW index for an on-premise persistent store |
| Optional pgvector adapter | `knowledge/pgvector.py` | dependency-injected retrieval against the HMIS PostgreSQL database |

Phase 1 capabilities: patient summary, documentation draft, knowledge assistant, duplicate detection,
queue intelligence, revenue leakage / billing anomalies, feedback intelligence.

The gateway has **no write path** into any Medilink module. `HMISReader` is read-only; a human
"accepted/edited/rejected" decision is only recorded in the audit log, and saving to the EMR remains the
domain module's job.

## Run
On Debian/Parrot, use a virtual environment; do not use `--break-system-packages`.

    python3 -m venv .venv
    .venv/bin/python -m pip install -r requirements.txt
    .venv/bin/python -m pytest -q
    MEDILINK_MOCK_LLM=1 .venv/bin/uvicorn medilink_ai.app:create_app --factory --port 8088
    curl -H "X-User-Id: dr.amina" localhost:8088/v1/summary/P123

## PostgreSQL foundation (Step 5.1)

The database layer is optional and lazy-loaded, so the existing JSON retrieval
path still works when database dependencies or `DATABASE_URL` are absent. To
enable it, install the added SQLAlchemy/psycopg/pgvector dependencies inside
the virtual environment, copy `.env.example` to `.env`, set `DATABASE_URL`,
then run `pytest -q tests/db`. The database checks are skipped intentionally
when no URL is configured.

## Local Ollama setup (Step 2)

The default local runtime is Ollama's native API. In a separate terminal, start
Ollama and install the initial CPU-friendly model once:

    ollama serve
    ollama pull qwen2.5:0.5b
    curl -sS http://127.0.0.1:11434/api/tags

Start the gateway with the same model name:

    export MEDILINK_LLM_URL=http://127.0.0.1:11434
    export MEDILINK_LLM_MODEL=qwen2.5:0.5b
    export MEDILINK_LLM_PROTOCOL=ollama
    .venv/bin/uvicorn medilink_ai.app:create_app --factory --port 8088

The gateway calls Ollama's `/api/chat` endpoint with non-streaming output and
bounded context, generation length, and CPU thread count. It returns a safe
`unavailable` result if Ollama is stopped or cannot complete a response.

For vLLM or llama.cpp, set `MEDILINK_LLM_PROTOCOL=openai-compatible` and use an
OpenAI-compatible `/v1/chat/completions` endpoint. All model endpoints must be
loopback, private-network addresses, or explicitly allow-listed; public AI APIs
are rejected.

## Production Medilink integration
Set `MEDILINK_AUTH_MODE=medilink`, `MEDILINK_BACKEND_URL` to the private Medilink API address,
and optionally `MEDILINK_BACKEND_ALLOWED_HOSTS` for a private DNS name. The gateway requires a
normal `Authorization: Bearer <Medilink JWT>` header and uses `/security/access/me` plus
`/patients/:id`; it does not validate a copied JWT secret, connect to PostgreSQL, or hold a
privileged AI account. Patient visibility is therefore enforced by Medilink itself.

Production requests should be made with the logged-in user's bearer token. Configure dedicated
`ai.*` permissions in Medilink RBAC as they become available; current role mappings are a
conservative compatibility fallback and should not be treated as a replacement for RBAC grants.

Every successful AI response includes model version, evidence count, source references and an
evidence-strength label. Generated clinical text is not duplicated in the audit database: audit
entries retain its SHA-256 digest and length instead.

Approved Markdown knowledge documents may include metadata in their first 20 lines:

    version: 3.2
    allowed_roles: doctor,nurse
    facility_id: facility-uuid   # optional; omit for all facilities
    classification: INTERNAL

Documents without `allowed_roles` are available to authenticated users. Restricted documents
must always declare their roles and, where relevant, a facility.

## Before any clinical use
1. Configure the production Medilink identity bridge described above and validate it with role and patient-visibility tests.
2. Choose the model by evaluating candidates on your hardware with clinician-written test cases
   (summary accuracy, hallucination rate, English/Kiswahili) - not by leaderboard.
3. Replace the sample policies in `knowledge/` with approved ones.
4. The regex safety layer is a backstop, not the main control. Add clinical safety review and a red-team test set.
5. Queue forecast is a simple formula; swap in a validated learned model once you have hospital history.
6. Add backend-owned, read-only adapters for orders, results, encounters, billing, queues, feedback and incidents before enabling their AI capabilities.
7. Complete DPIA, lawful basis, encrypted audit retention/backups, incident response, model approval/rollback and clinical governance review.

## Step 5: persistent semantic retrieval

The default development store is the atomic JSON file under `data/knowledge/processed`.
For production, review and apply the isolated schema to the private HMIS PostgreSQL database
(the `vector` extension must be enabled in that database):

    psql "$DATABASE_URL" -f sql/001_knowledge_pgvector.sql

`knowledge/pgvector.py` provides a database adapter through a deployment-owned connection
factory. It applies organization, facility, department, role/user, classification, and effective
date filters before returning evidence. Do not add a second database password to the AI service;
reuse the protected deployment secret and keep the adapter read-only unless a separately reviewed
ingestion worker is enabled.

The built-in hashing embedder is deterministic and offline. It is a retrieval fallback, not a
clinical model. A locally hosted embedding service can replace `EmbeddingService` without
changing authorization, evidence, citation, or no-evidence behavior.
