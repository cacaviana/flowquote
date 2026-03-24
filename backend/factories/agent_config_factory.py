from datetime import datetime, timezone


class AgentConfigFactory:
    """Cria documentos de agent_config para persistencia."""

    _DEFAULTS = {
        "devis": {
            "model_name": "openai:gpt-4o-mini",
            "instructions": "Vous êtes un expert en génération de devis...",
            "output_format": "quote",
        },
        "agendamento": {
            "model_name": "openai:gpt-4o-mini",
            "instructions": "Vous êtes un assistant de prise de rendez-vous...",
            "output_format": "booking_summary",
        },
    }

    @staticmethod
    def create_default(module: str) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        defaults = AgentConfigFactory._DEFAULTS.get(module, {})
        return {
            "module": module,
            "model_name": defaults.get("model_name", "openai:gpt-4o-mini"),
            "instructions": defaults.get("instructions", ""),
            "output_format": defaults.get("output_format", ""),
            "created_at": now,
            "updated_at": now,
        }
