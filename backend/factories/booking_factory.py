from datetime import datetime, timezone


class BookingFactory:
    """Cria documentos de booking para persistencia."""

    @staticmethod
    def create_new(data: dict) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        return {
            "flow_id": data.get("flow_id", ""),
            "flow_slug": data.get("flow_slug", ""),
            "tenant_id": data.get("tenant_id", "tenant_1"),
            "client_name": data.get("client_name", ""),
            "client_email": data.get("client_email", ""),
            "client_phone": data.get("client_phone"),
            "booking_date": data.get("booking_date", ""),
            "booking_time": data.get("booking_time", ""),
            "answers": data.get("answers", []),
            "status": "pending",
            "created_at": now,
            "updated_at": now,
        }
