from functools import lru_cache

from .base import InferenceProvider
from .ollama_provider import OllamaInferenceProvider


@lru_cache(maxsize=1)
def get_inference_provider() -> InferenceProvider:
    return OllamaInferenceProvider()
