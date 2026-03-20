from fastapi import APIRouter, HTTPException
from dtos.booking.create_booking.request import CreateBookingRequest
from dtos.booking.create_booking.response import CreateBookingResponse
from services.booking_service import BookingService

router = APIRouter(prefix="/api/bookings", tags=["bookings"])

_service = BookingService()


@router.get("/days")
async def get_available_days():
    """Retorna os proximos 7 dias uteis disponiveis."""
    return await _service.get_available_days()


@router.get("/slots")
async def get_slots(date: str):
    """Retorna slots disponiveis para uma data (YYYY-MM-DD)."""
    return await _service.get_available_slots(date)


@router.get("")
async def list_bookings():
    """Lista todos os agendamentos (admin)."""
    return await _service.list_all()


@router.get("/flow/{flow_id}")
async def list_by_flow(flow_id: str):
    """Lista agendamentos de um flow especifico."""
    return await _service.list_by_flow(flow_id)


@router.get("/{booking_id}")
async def get_booking(booking_id: str):
    """Busca agendamento por ID."""
    result = await _service.get_by_id(booking_id)
    if not result:
        raise HTTPException(status_code=404, detail="Agendamento nao encontrado")
    return result


@router.post("", status_code=201, response_model=CreateBookingResponse)
async def create_booking(request: CreateBookingRequest):
    """Cria agendamento."""
    try:
        result = await _service.create(request.model_dump())
        return CreateBookingResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/{booking_id}", status_code=204)
async def delete_booking(booking_id: str):
    """Remove agendamento."""
    deleted = await _service.delete(booking_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Agendamento nao encontrado")
