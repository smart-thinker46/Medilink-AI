from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    project_root: str = os.getenv("MEDILINK_AI_PROJECT_ROOT", str(Path(__file__).resolve().parent.parent))
    knowledge_store: str = os.getenv("MEDILINK_KNOWLEDGE_STORE", "")
    # Any OpenAI-compatible server running INSIDE the hospital (Ollama, vLLM, llama.cpp server).
    llm_base_url: str = os.getenv("MEDILINK_LLM_URL", "http://127.0.0.1:11434")
    llm_model: str = os.getenv("MEDILINK_LLM_MODEL", "local-model")
    # Ollama uses /api/chat; vLLM and llama.cpp normally expose the OpenAI
    # compatible /v1/chat/completions endpoint. Both remain local-only.
    llm_protocol: str = os.getenv("MEDILINK_LLM_PROTOCOL", "ollama").strip().lower()
    ollama_keep_alive: str = os.getenv("MEDILINK_OLLAMA_KEEP_ALIVE", "10m")
    ollama_num_ctx: int = int(os.getenv("MEDILINK_OLLAMA_NUM_CTX", "1024"))
    ollama_num_predict: int = int(os.getenv("MEDILINK_OLLAMA_NUM_PREDICT", "512"))
    ollama_num_thread: int = int(os.getenv("MEDILINK_OLLAMA_NUM_THREAD", "4"))
    model_version: str = os.getenv("MEDILINK_MODEL_VERSION", "medilink-ai-0.1")
    # Hostnames besides loopback/private IPs that the gateway may talk to (e.g. "ai-server.hospital.lan").
    allowed_hosts: tuple = tuple(h for h in os.getenv("MEDILINK_ALLOWED_HOSTS", "").split(",") if h)
    audit_db: str = os.getenv("MEDILINK_AUDIT_DB", "medilink_ai_audit.db")
    knowledge_dir: str = os.getenv("MEDILINK_KNOWLEDGE_DIR", "knowledge")
    use_mock_llm: bool = os.getenv("MEDILINK_MOCK_LLM", "0") == "1"
    temperature: float = 0.1
    request_timeout_s: float = 120.0
    # Below this BM25 score the knowledge assistant answers "not found" without calling the LLM.
    rag_min_score: float = 1.0
    rag_top_k: int = 4
    # Production identity and data access are delegated to the existing Medilink
    # backend.  The demo mode exists only for local tests and demonstrations.
    auth_mode: str = os.getenv("MEDILINK_AUTH_MODE", "demo")  # demo | medilink
    backend_base_url: str = os.getenv("MEDILINK_BACKEND_URL", "http://127.0.0.1:3000")
    backend_allowed_hosts: tuple = tuple(h for h in os.getenv("MEDILINK_BACKEND_ALLOWED_HOSTS", "").split(",") if h)
    backend_timeout_s: float = float(os.getenv("MEDILINK_BACKEND_TIMEOUT_S", "10"))
    # A small in-memory guard against accidental loops or a compromised UI. In
    # production it should be complemented by an ingress/distributed limiter.
    request_rate_per_minute: int = int(os.getenv("MEDILINK_AI_RATE_PER_MINUTE", "30"))
    max_transcript_chars: int = int(os.getenv("MEDILINK_AI_MAX_TRANSCRIPT_CHARS", "12000"))
    environment: str = os.getenv("MEDILINK_ENV", "development")
    cors_origins: tuple = tuple(origin.strip() for origin in os.getenv(
        "MEDILINK_AI_CORS_ORIGINS", "http://localhost:3001,http://127.0.0.1:3001"
    ).split(",") if origin.strip())

    def resolved_knowledge_store(self) -> Path:
        return Path(self.knowledge_store or (Path(self.project_root) / "data" / "knowledge" / "processed" / "knowledge.json"))
