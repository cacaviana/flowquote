from config.settings import settings
from data.repositories.mongo.settings_repository import SettingsRepository

AVAILABLE_MODELS: dict[str, list[dict]] = {
    "anthropic": [
        {"id": "claude-sonnet-4-20250514", "label": "Claude Sonnet 4"},
        {"id": "claude-opus-4-6", "label": "Claude Opus 4.6"},
    ],
    "openai": [
        {"id": "gpt-4o", "label": "GPT-4o"},
        {"id": "gpt-4.5-preview", "label": "GPT-4.5"},
    ],
}

_VALID_PROVIDERS = set(AVAILABLE_MODELS.keys())
_VALID_MODELS = {m["id"] for models in AVAILABLE_MODELS.values() for m in models}


class SettingsService:

    def __init__(self):
        self._repo = SettingsRepository()

    async def get_ai_config(self) -> dict:
        """Retorna config de IA atual. DB tem prioridade sobre .env."""
        doc = await self._repo.get_ai_config()
        if doc:
            return {"provider": doc["provider"], "model": doc["model"]}
        # fallback para .env
        provider = settings.ai_provider.lower()
        if provider == "anthropic":
            return {"provider": "anthropic", "model": settings.anthropic_model}
        return {"provider": "openai", "model": settings.openai_model}

    async def update_ai_config(self, provider: str, model: str) -> dict:
        """Valida e persiste a configuracao de IA."""
        if provider not in _VALID_PROVIDERS:
            raise ValueError(f"Provedor invalido: '{provider}'. Opcoes: {sorted(_VALID_PROVIDERS)}")
        if model not in _VALID_MODELS:
            raise ValueError(f"Modelo invalido: '{model}'.")
        await self._repo.save_ai_config(provider, model)
        return {"provider": provider, "model": model}
