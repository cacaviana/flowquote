from pydantic import BaseModel, Field, field_validator
from typing import Optional


class CreateBookingRequest(BaseModel):
    flow_id: str = Field(..., min_length=1)
    flow_slug: str = Field(..., min_length=1)
    client_name: str = Field(..., min_length=1)
    client_email: str = Field(..., min_length=1)
    client_phone: Optional[str] = None
    booking_date: str = Field(..., description="YYYY-MM-DD")
    booking_time: str = Field(..., description="HH:MM")
    answers: list[dict] = Field(default_factory=list)
    tenant_id: Optional[str] = Field(default="tenant_1")

    @field_validator("booking_date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        from datetime import date
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError("booking_date deve ser YYYY-MM-DD")
        return v

    @field_validator("booking_time")
    @classmethod
    def validate_time(cls, v: str) -> str:
        allowed = {"09:00", "10:00", "11:00", "14:00", "15:00", "16:00"}
        if v not in allowed:
            raise ValueError(f"Horario invalido. Opcoes: {sorted(allowed)}")
        return v
