from config.database import mongodb_client

_COLLECTION = "agents"


class AgentConfigRepository:
    """Acesso ao MongoDB para configuracoes de agentes."""

    @property
    def _col(self):
        return mongodb_client.database[_COLLECTION]

    async def find_by_module(self, module: str) -> dict | None:
        return await self._col.find_one({"module": module})

    async def upsert_by_module(self, module: str, doc: dict) -> str:
        result = await self._col.find_one_and_update(
            {"module": module},
            {"$set": doc},
            upsert=True,
            return_document=True,
        )
        return str(result["_id"])

    async def find_all(self) -> list[dict]:
        cursor = self._col.find()
        return await cursor.to_list(length=1000)
