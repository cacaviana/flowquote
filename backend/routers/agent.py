from fastapi import APIRouter
from services.quote_generator import quote_agent, _get_model_name, QuoteOutput

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.get("/info")
async def agent_info():
    """Retorna informacoes do agente IA (somente leitura)."""
    instructions = quote_agent._instructions
    if isinstance(instructions, list):
        instructions = "\n".join(instructions)

    return {
        "model": _get_model_name(),
        "instructions": instructions or "",
        "output_schema": QuoteOutput.model_json_schema(),
    }
