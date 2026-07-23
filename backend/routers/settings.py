from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from config.database import mongodb_client
from dependencies.tenant import TenantContext, get_tenant_context

router = APIRouter(prefix="/api/settings", tags=["settings"])

COLLECTION = "settings"
LEGACY_DOC_ID = "ai_settings"

MODELS = {
    "anthropic": [
        {"id": "claude-sonnet-4-20250514", "label": "Claude Sonnet 4"},
        {"id": "claude-opus-4-6", "label": "Claude Opus 4.6"},
    ],
    "openai": [
        {"id": "gpt-4o", "label": "GPT-4o"},
        {"id": "gpt-4.5-preview", "label": "GPT-4.5"},
    ],
}


class AiSettingsRequest(BaseModel):
    provider: str
    model: str


def _doc_id(tenant_id: Optional[str]) -> str:
    return f"{LEGACY_DOC_ID}:{tenant_id}" if tenant_id else LEGACY_DOC_ID


async def get_ai_config(tenant_id: Optional[str] = None) -> dict:
    """Retorna config de IA atual (doc do tenant > doc legado > .env)."""
    from config.settings import settings

    doc = None
    if tenant_id:
        doc = await mongodb_client.database[COLLECTION].find_one({"_id": _doc_id(tenant_id)})
    if not doc:
        doc = await mongodb_client.database[COLLECTION].find_one({"_id": LEGACY_DOC_ID})
    if doc:
        return {"provider": doc["provider"], "model": doc["model"]}
    # fallback para .env
    provider = settings.ai_provider.lower()
    if provider == "anthropic":
        return {"provider": "anthropic", "model": settings.anthropic_model}
    return {"provider": "openai", "model": settings.openai_model}


@router.get("/ai")
async def get_ai_settings(ctx: TenantContext = Depends(get_tenant_context)):
    config = await get_ai_config(tenant_id=ctx.tenant_id)
    return {**config, "available_models": MODELS}


@router.put("/ai")
async def update_ai_settings(body: AiSettingsRequest, ctx: TenantContext = Depends(get_tenant_context)):
    await mongodb_client.database[COLLECTION].update_one(
        {"_id": _doc_id(ctx.tenant_id)},
        {"$set": {"provider": body.provider, "model": body.model, "tenant_id": ctx.tenant_id}},
        upsert=True,
    )
    return {"provider": body.provider, "model": body.model}
