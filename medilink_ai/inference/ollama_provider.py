from __future__ import annotations

import httpx

from ..llm import assert_local_endpoint
from .base import InferenceProvider
from .config import OLLAMA_BASE_URL, OLLAMA_KEEP_ALIVE, OLLAMA_TIMEOUT_SECONDS
from .models import GenerationRequest, GenerationResponse


class OllamaInferenceProvider(InferenceProvider):
    def __init__(self, base_url: str = OLLAMA_BASE_URL, timeout_seconds: float = OLLAMA_TIMEOUT_SECONDS, allowed_hosts: tuple[str, ...] = ()) -> None:
        assert_local_endpoint(base_url, allowed_hosts)
        self.base_url = base_url.rstrip("/")
        self.timeout = httpx.Timeout(timeout_seconds, connect=10.0)

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        if not request.system_prompt.strip() or not request.user_prompt.strip():
            raise ValueError("system_prompt and user_prompt are required")
        if not 0 <= request.temperature <= 2:
            raise ValueError("temperature must be between 0 and 2")
        if not 1 <= request.max_tokens <= 8192:
            raise ValueError("max_tokens must be between 1 and 8192")
        payload = {
            "model": request.model,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt},
            ],
            "stream": False,
            "keep_alive": OLLAMA_KEEP_ALIVE,
            "options": {"temperature": request.temperature, "num_predict": request.max_tokens},
        }
        if request.response_format:
            payload["format"] = request.response_format
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
            content = data.get("message", {}).get("content", "")
            if not isinstance(content, str) or not content.strip():
                raise ValueError("Ollama returned an empty response")
            return GenerationResponse(
                content=content,
                model=str(data.get("model") or request.model),
                prompt_tokens=data.get("prompt_eval_count"),
                completion_tokens=data.get("eval_count"),
                total_duration_ns=data.get("total_duration"),
                load_duration_ns=data.get("load_duration"),
                prompt_duration_ns=data.get("prompt_eval_duration"),
                generation_duration_ns=data.get("eval_duration"),
            )
        except (httpx.HTTPError, ValueError, TypeError, KeyError) as exc:
            raise RuntimeError("The local Ollama inference provider is unavailable.") from exc

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
            return True
        except httpx.HTTPError:
            return False
