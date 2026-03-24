from fastapi import APIRouter, Query
from schemas.quote import QuoteOutput
from services.agent_service import AGENT_INSTRUCTIONS, get_model_name
from data.repositories.mongo.agent_config_repository import AgentConfigRepository

router = APIRouter(prefix="/api/agent", tags=["agent"])

_config_repo = AgentConfigRepository()


@router.get("/info")
async def agent_info(module: str = Query(default="devis")):
    """Retorna informacoes do agente IA (somente leitura).

    Se existir config no MongoDB para o modulo, usa ela.
    Senao, cai nos defaults hardcoded (devis).
    """
    config = await _config_repo.find_by_module(module)

    if config:
        return {
            "module": module,
            "model": config.get("model_name", await get_model_name()),
            "instructions": config.get("instructions", AGENT_INSTRUCTIONS),
            "output_schema": QuoteOutput.model_json_schema(),
        }

    return {
        "module": module,
        "model": await get_model_name(),
        "instructions": AGENT_INSTRUCTIONS,
        "output_schema": QuoteOutput.model_json_schema(),
    }
