from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.settings_service import AVAILABLE_MODELS, SettingsService

router = APIRouter(prefix="/api/settings", tags=["settings"])

_service = SettingsService()


class AiSettingsRequest(BaseModel):
    provider: str
    model: str


@router.get("/ai")
async def get_ai_settings():
    config = await _service.get_ai_config()
    return {**config, "available_models": AVAILABLE_MODELS}


@router.put("/ai")
async def update_ai_settings(body: AiSettingsRequest):
    try:
        return await _service.update_ai_config(body.provider, body.model)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
