class BookingMapper:
    """Conversoes entre documento MongoDB e DTOs de booking."""

    @staticmethod
    def to_response(doc: dict) -> dict:
        return {
            "id": str(doc.get("_id", "")),
            "flow_id": doc.get("flow_id", ""),
            "flow_slug": doc.get("flow_slug", ""),
            "client_name": doc.get("client_name", ""),
            "client_email": doc.get("client_email", ""),
            "client_phone": doc.get("client_phone"),
            "booking_date": doc.get("booking_date", ""),
            "booking_time": doc.get("booking_time", ""),
            "answers": doc.get("answers", []),
            "status": doc.get("status", "pending"),
            "created_at": str(doc.get("created_at", "")),
        }

    @staticmethod
    def to_summary(doc: dict) -> dict:
        return {
            "id": str(doc.get("_id", "")),
            "flow_id": doc.get("flow_id", ""),
            "flow_slug": doc.get("flow_slug", ""),
            "client_name": doc.get("client_name", ""),
            "client_email": doc.get("client_email", ""),
            "client_phone": doc.get("client_phone"),
            "booking_date": doc.get("booking_date", ""),
            "booking_time": doc.get("booking_time", ""),
            "status": doc.get("status", "pending"),
            "has_answers": len(doc.get("answers", [])) > 0,
            "created_at": str(doc.get("created_at", "")),
        }
