from pydantic import BaseModel
from typing import Optional


class BookingSummary(BaseModel):
    id: str
    flow_id: str
    flow_slug: str
    client_name: str
    client_email: str
    client_phone: Optional[str]
    booking_date: str
    booking_time: str
    status: str
    has_answers: bool
    created_at: str


class ListBookingsResponse(BaseModel):
    bookings: list[BookingSummary]
    total: int
