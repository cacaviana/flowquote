from fastapi import APIRouter, Depends, HTTPException
from dtos.flow.save_flow.request import SaveFlowRequest
from services.flow_service import FlowService
from dependencies.tenant import TenantContext, get_tenant_context

router = APIRouter(prefix="/api/flows", tags=["flows"])

_service = FlowService()


@router.get("")
async def list_flows(ctx: TenantContext = Depends(get_tenant_context)):
    """Lista todos os flows do tenant (admin)."""
    return await _service.list_all(tenant_id=ctx.tenant_id)


@router.get("/{flow_id}")
async def get_flow(flow_id: str, ctx: TenantContext = Depends(get_tenant_context)):
    """Busca flow por ID, escopado ao tenant (admin)."""
    result = await _service.get_by_id(flow_id, tenant_id=ctx.tenant_id)
    if not result:
        raise HTTPException(status_code=404, detail="Flow nao encontrado")
    return result


@router.get("/slug/{slug}")
async def get_flow_by_slug(slug: str):
    """Busca flow por slug (URL PUBLICA do formulario do cliente final).

    Sem auth: o tenant e resolvido pelo proprio documento do flow —
    nunca vem do cliente.
    """
    result = await _service.get_by_slug(slug)
    if not result:
        raise HTTPException(status_code=404, detail="Flow nao encontrado")
    return result


@router.post("", status_code=201)
async def create_flow(request: SaveFlowRequest, ctx: TenantContext = Depends(get_tenant_context)):
    """Cria novo flow no tenant do usuario autenticado (admin)."""
    try:
        return await _service.create(request.model_dump(), tenant_id=ctx.tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.put("/{flow_id}")
async def update_flow(
    flow_id: str,
    request: SaveFlowRequest,
    ctx: TenantContext = Depends(get_tenant_context),
):
    """Atualiza flow existente, escopado ao tenant (admin)."""
    try:
        result = await _service.update(flow_id, request.model_dump(), tenant_id=ctx.tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if not result:
        raise HTTPException(status_code=404, detail="Flow nao encontrado")
    return result


@router.delete("/{flow_id}", status_code=204)
async def delete_flow(flow_id: str, ctx: TenantContext = Depends(get_tenant_context)):
    """Remove flow, escopado ao tenant (admin)."""
    deleted = await _service.delete(flow_id, tenant_id=ctx.tenant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Flow nao encontrado")
