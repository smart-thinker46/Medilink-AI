from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
except ImportError:  # pragma: no cover
    pass

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", os.getenv("MEDILINK_LLM_URL", "http://127.0.0.1:11434")).rstrip("/")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", os.getenv("MEDILINK_LLM_MODEL", "qwen2.5:0.5b"))
OLLAMA_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "180"))
OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.1"))
OLLAMA_NUM_PREDICT = int(os.getenv("OLLAMA_NUM_PREDICT", "400"))
OLLAMA_KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", os.getenv("MEDILINK_OLLAMA_KEEP_ALIVE", "5m"))
