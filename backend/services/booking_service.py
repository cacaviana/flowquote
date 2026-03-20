"""Servico de agendamento.

Slots disponiveis sao fixos (mocked MVP):
  09:00, 10:00, 11:00, 14:00, 15:00, 16:00
Dias disponiveis: proximos 7 dias uteis (seg-sex) a partir de amanha.
"""

from datetime import date, timedelta
from typing import Optional

from data.repositories.mongo.booking_repository import BookingRepository
from factories.booking_factory import BookingFactory
from mappers.booking_mapper import BookingMapper

_ALL_SLOTS = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]


def _next_business_days(n: int = 7) -> list[str]:
    """Retorna os proximos n dias uteis (seg-sex) a partir de amanha."""
    days = []
    cursor = date.today() + timedelta(days=1)
    while len(days) < n:
        if cursor.weekday() < 5:  # 0=seg, 4=sex
            days.append(cursor.isoformat())
        cursor += timedelta(days=1)
    return days


class BookingService:

    def __init__(self):
        self._repo = BookingRepository()
        self._factory = BookingFactory
        self._mapper = BookingMapper

    async def get_available_slots(self, date_str: str) -> dict:
        """Retorna slots disponiveis para uma data."""
        available_days = _next_business_days(14)
        if date_str not in available_days:
            return {"date": date_str, "available": [], "message": "Data indisponivel"}
        taken = await self._repo.find_slots_taken(date_str)
        available = [s for s in _ALL_SLOTS if s not in taken]
        return {"date": date_str, "available": available, "all_slots": _ALL_SLOTS, "taken": taken}

    async def get_available_days(self) -> dict:
        """Retorna os proximos dias uteis disponiveis."""
        days = _next_business_days(7)
        return {"days": days}

    async def create(self, data: dict) -> dict:
        date_str = data.get("booking_date", "")
        time_str = data.get("booking_time", "")
        email = data.get("client_email", "")

        # RN-003: sem duplicata de email no mesmo slot
        if await self._repo.check_duplicate(email, date_str, time_str):
            raise ValueError("Este email ja possui agendamento neste horario")

        # RN-001: verifica se slot ainda disponivel
        taken = await self._repo.find_slots_taken(date_str)
        if time_str in taken:
            raise ValueError(f"Horario {time_str} nao esta mais disponivel")

        doc = self._factory.create_new(data)
        saved = await self._repo.insert(doc)
        return self._mapper.to_response(saved)

    async def list_all(self) -> dict:
        docs = await self._repo.find_all()
        return {"bookings": [self._mapper.to_summary(d) for d in docs], "total": len(docs)}

    async def list_by_flow(self, flow_id: str) -> dict:
        docs = await self._repo.find_by_flow(flow_id)
        return {"bookings": [self._mapper.to_summary(d) for d in docs], "total": len(docs)}

    async def get_by_id(self, id: str) -> Optional[dict]:
        doc = await self._repo.find_by_id(id)
        return self._mapper.to_response(doc) if doc else None

    async def delete(self, id: str) -> bool:
        return await self._repo.delete(id)
