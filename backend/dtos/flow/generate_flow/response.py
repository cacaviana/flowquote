from pydantic import BaseModel, Field


class GenerateFlowResponse(BaseModel):
    flow: dict
    avisos: list[str] = Field(default=[])
    tokens_input: int = 0
    tokens_output: int = 0
