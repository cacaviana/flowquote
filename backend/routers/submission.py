from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from dtos.submission.create_submission.request import CreateSubmissionRequest
from dtos.submission.create_submission.response import CreateSubmissionResponse
from services.submission_service import SubmissionService

router = APIRouter(prefix="/api/submissions", tags=["submissions"])

_service = SubmissionService()


@router.get("")
async def list_submissions():
    """Lista todas as submissions."""
    return await _service.list_all()


@router.get("/flow/{flow_id}")
async def list_by_flow(flow_id: str):
    """Lista submissions de um flow especifico."""
    return await _service.list_by_flow(flow_id)


@router.get("/{submission_id}")
async def get_submission(submission_id: str):
    """Busca submission por ID."""
    result = await _service.get_by_id(submission_id)
    if not result:
        raise HTTPException(status_code=404, detail="Submission nao encontrada")
    return result


@router.post("", status_code=201, response_model=CreateSubmissionResponse)
async def create_submission(request: CreateSubmissionRequest):
    """Cria submission e gera orcamento se aplicavel."""
    try:
        result = await _service.create(request.model_dump())
        return CreateSubmissionResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/{submission_id}/export", response_class=PlainTextResponse)
async def export_submission(submission_id: str):
    """Exporta devis como texto e salva localmente."""
    result = await _service.export(submission_id)
    if not result:
        raise HTTPException(status_code=404, detail="Submission nao encontrada")
    return PlainTextResponse(
        content=result["content"],
        headers={
            "Content-Disposition": f'attachment; filename="{result["filename"]}"',
            "X-Saved-Path": result["filepath"],
        },
    )


@router.delete("/{submission_id}", status_code=204)
async def delete_submission(submission_id: str):
    """Remove submission."""
    deleted = await _service.delete(submission_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Submission nao encontrada")
