from fastapi import APIRouter
from schemas.quote import QuoteOutput
from services.agent_service import AGENT_INSTRUCTIONS, get_model_name

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.get("/info")
async def agent_info():
    """Retorna informacoes do agente IA (somente leitura)."""
    return {
        "model": await get_model_name(),
        "instructions": AGENT_INSTRUCTIONS,
        "output_schema": QuoteOutput.model_json_schema(),
    }
