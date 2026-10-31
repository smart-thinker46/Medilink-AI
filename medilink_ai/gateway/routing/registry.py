from __future__ import annotations

from collections.abc import Iterable

from .models import ModelAvailability, ModelCapability, ModelDefinition


def get_default_model_registry() -> tuple[ModelDefinition, ...]:
    # Development-only registry. Sensitive models remain unregistered until approved.
    return (
        ModelDefinition(
            model_id="knowledge-small", provider="ollama", model_name="qwen2.5:0.5b",
            capabilities=frozenset({ModelCapability.KNOWLEDGE, ModelCapability.GENERAL}),
            priority=10, max_input_tokens=4096, max_output_tokens=400, temperature=0.1,
            availability=ModelAvailability.AVAILABLE, supports_json=True,
        ),
    )


class ModelRegistry:
    def __init__(self, models: Iterable[ModelDefinition] | None = None):
        definitions = tuple(models) if models is not None else get_default_model_registry()
        if len({model.model_id for model in definitions}) != len(definitions):
            raise ValueError("Model IDs must be unique.")
        self._models = {model.model_id: model for model in definitions}

    def all(self) -> tuple[ModelDefinition, ...]:
        return tuple(sorted(self._models.values(), key=lambda model: (model.priority, model.model_id)))

    def get(self, model_id: str) -> ModelDefinition | None:
        return self._models.get(model_id)
