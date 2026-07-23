from fastapi import APIRouter, Depends
from services.quote_generator import _get_model_name, _AGENT_INSTRUCTIONS, QuoteOutput
from dependencies.tenant import TenantContext, get_tenant_context

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.get("/info")
async def agent_info(ctx: TenantContext = Depends(get_tenant_context)):
    """Retorna informacoes do agente IA (somente leitura, admin)."""
    return {
        "model": await _get_model_name(tenant_id=ctx.tenant_id),
        "instructions": _AGENT_INSTRUCTIONS,
        "output_schema": QuoteOutput.model_json_schema(),
    }
