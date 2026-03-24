class AgentConfigMapper:
    """Conversoes entre documento MongoDB e DTOs de agent_config."""

    @staticmethod
    def to_response(doc: dict) -> dict:
        return {
            "id": str(doc.get("_id", "")),
            "module": doc.get("module", ""),
            "model_name": doc.get("model_name", ""),
            "instructions": doc.get("instructions", ""),
            "output_format": doc.get("output_format", ""),
            "created_at": str(doc.get("created_at", "")),
            "updated_at": str(doc.get("updated_at", "")),
        }
