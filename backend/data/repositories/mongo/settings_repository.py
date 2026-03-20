from config.database import mongodb_client

_COLLECTION = "settings"
_DOC_ID = "ai_settings"


class SettingsRepository:
    """Acesso ao MongoDB para configuracoes da aplicacao."""

    async def get_ai_config(self) -> dict | None:
        return await mongodb_client.database[_COLLECTION].find_one({"_id": _DOC_ID})

    async def save_ai_config(self, provider: str, model: str) -> None:
        await mongodb_client.database[_COLLECTION].update_one(
            {"_id": _DOC_ID},
            {"$set": {"provider": provider, "model": model}},
            upsert=True,
        )
