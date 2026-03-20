from bson import ObjectId
from config.database import mongodb_client

_COLLECTION = "bookings"


class BookingRepository:
    """Acesso ao MongoDB para agendamentos."""

    @property
    def _col(self):
        return mongodb_client.database[_COLLECTION]

    async def find_all(self) -> list[dict]:
        cursor = self._col.find().sort("booking_date", -1)
        return await cursor.to_list(length=1000)

    async def find_by_flow(self, flow_id: str) -> list[dict]:
        cursor = self._col.find({"flow_id": flow_id}).sort("booking_date", -1)
        return await cursor.to_list(length=1000)

    async def find_by_id(self, id: str) -> dict | None:
        try:
            return await self._col.find_one({"_id": ObjectId(id)})
        except Exception:
            return None

    async def find_slots_taken(self, date: str) -> list[str]:
        """Retorna lista de horarios ja ocupados para uma data."""
        cursor = self._col.find(
            {"booking_date": date, "status": {"$ne": "cancelled"}},
            {"booking_time": 1}
        )
        docs = await cursor.to_list(length=100)
        return [d["booking_time"] for d in docs]

    async def check_duplicate(self, email: str, date: str, time: str) -> bool:
        """Verifica se email ja tem booking nesse slot."""
        doc = await self._col.find_one({
            "client_email": email,
            "booking_date": date,
            "booking_time": time,
            "status": {"$ne": "cancelled"},
        })
        return doc is not None

    async def insert(self, doc: dict) -> dict:
        result = await self._col.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    async def delete(self, id: str) -> bool:
        try:
            result = await self._col.delete_one({"_id": ObjectId(id)})
            return result.deleted_count > 0
        except Exception:
            return False
