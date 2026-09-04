from pydantic import BaseModel, Field


class GenerateFlowRequest(BaseModel):
    """Descricao textual do fluxo desejado (v1: somente texto, sem uploads)."""
    description: str = Field(..., min_length=120, max_length=4000)
