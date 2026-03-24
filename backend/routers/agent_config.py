from fastapi import APIRouter, HTTPException
from data.repositories.mongo.agent_config_repository import AgentConfigRepository
from factories.agent_config_factory import AgentConfigFactory
from mappers.agent_config_mapper import AgentConfigMapper

router = APIRouter(prefix="/api/agent-configs", tags=["agent-config"])

_repo = AgentConfigRepository()


@router.get("")
async def list_configs():
    """Lista todas as configuracoes de agentes."""
    docs = await _repo.find_all()
    return [AgentConfigMapper.to_response(d) for d in docs]


@router.get("/{module}")
async def get_config(module: str):
    """Retorna config do agente para um modulo (cria default se nao existir)."""
    doc = await _repo.find_by_module(module)
    if not doc:
        default = AgentConfigFactory.create_default(module)
        await _repo.upsert_by_module(module, default)
        doc = await _repo.find_by_module(module)
    return AgentConfigMapper.to_response(doc)


@router.put("/{module}")
async def update_config(module: str, body: dict):
    """Atualiza config do agente para um modulo."""
    from datetime import datetime, timezone
    allowed = {"model_name", "instructions", "output_format"}
    update = {k: v for k, v in body.items() if k in allowed}
    if not update:
        raise HTTPException(400, "Nenhum campo valido para atualizar")
    update["updated_at"] = datetime.now(timezone.utc).isoformat()
    await _repo.upsert_by_module(module, update)
    doc = await _repo.find_by_module(module)
    return AgentConfigMapper.to_response(doc)


@router.post("/seed")
async def seed_configs():
    """Cria configs default para todos os modulos (se nao existirem)."""
    created = []
    for module in ("devis", "agendamento"):
        existing = await _repo.find_by_module(module)
        if not existing:
            default = AgentConfigFactory.create_default(module)
            await _repo.upsert_by_module(module, default)
            created.append(module)
    return {"seeded": created}
