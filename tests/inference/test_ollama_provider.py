import httpx
import asyncio

from medilink_ai.inference.models import GenerationRequest
from medilink_ai.inference.ollama_provider import OllamaInferenceProvider


def test_ollama_provider_sends_json_format(monkeypatch):
    seen = {}

    async def fake_post(self, url, json):
        seen.update(json)
        return httpx.Response(200, request=httpx.Request("POST", url), json={"model": "test-model", "message": {"content": "{\"answer\":\"Hello\"}"}, "prompt_eval_count": 2})

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    provider = OllamaInferenceProvider("http://127.0.0.1:11434")
    response = asyncio.run(provider.generate(GenerationRequest("system", "question", "test-model")))
    assert response.content == '{"answer":"Hello"}'
    assert seen["format"] == "json"
    assert seen["stream"] is False
