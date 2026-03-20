from pydantic import BaseModel
from typing import Optional


class CreateBookingResponse(BaseModel):
    id: str
    flow_id: str
    flow_slug: str
    client_name: str
    client_email: str
    client_phone: Optional[str]
    booking_date: str
    booking_time: str
    status: str
    created_at: str
