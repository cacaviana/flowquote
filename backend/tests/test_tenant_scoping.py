"""Testes de escopo por tenant nos services — com fakes (sem rede)."""
import pytest

from services.flow_service import FlowService
from services.submission_service import SubmissionService


class FakeFlowRepository:
    """Fake do FlowRepository — grava as chamadas recebidas para inspecao."""

    def __init__(self, docs: list[dict]):
        self.docs = docs
        self.calls: list[tuple] = []

    async def find_all(self, tenant_id=None):
        self.calls.append(("find_all", tenant_id))
        return [d for d in self.docs if tenant_id is None or d.get("tenant_id") == tenant_id]

    async def find_by_id(self, id, tenant_id=None):
        self.calls.append(("find_by_id", id, tenant_id))
        for d in self.docs:
            if d["_id"] == id and (tenant_id is None or d.get("tenant_id") == tenant_id):
                return d
        return None

    async def find_by_slug(self, slug, tenant_id=None):
        self.calls.append(("find_by_slug", slug, tenant_id))
        for d in self.docs:
            if d["slug"] == slug and (tenant_id is None or d.get("tenant_id") == tenant_id):
                return d
        return None

    async def insert(self, document):
        document = {**document, "_id": "new_id"}
        self.docs.append(document)
        return document

    async def update(self, id, data, tenant_id=None):
        doc = await self.find_by_id(id, tenant_id)
        if not doc:
            return None
        doc.update(data)
        return doc

    async def delete(self, id, tenant_id=None):
        doc = await self.find_by_id(id, tenant_id)
        if doc:
            self.docs.remove(doc)
            return True
        return False


class FakeSubmissionRepository:
    def __init__(self, docs=None):
        self.docs = docs or []
        self.calls: list[tuple] = []
        self.inserted = None

    async def find_all(self, tenant_id=None):
        self.calls.append(("find_all", tenant_id))
        return [d for d in self.docs if tenant_id is None or d.get("tenant_id") == tenant_id]

    async def find_by_flow(self, flow_id, tenant_id=None):
        self.calls.append(("find_by_flow", flow_id, tenant_id))
        return [
            d for d in self.docs
            if d.get("flow_id") == flow_id
            and (tenant_id is None or d.get("tenant_id") == tenant_id)
        ]

    async def find_by_id(self, id, tenant_id=None):
        self.calls.append(("find_by_id", id, tenant_id))
        for d in self.docs:
            if d["_id"] == id and (tenant_id is None or d.get("tenant_id") == tenant_id):
                return d
        return None

    async def insert(self, document):
        self.inserted = {**document, "_id": "sub_1"}
        self.docs.append(self.inserted)
        return self.inserted

    async def delete(self, id, tenant_id=None):
        doc = await self.find_by_id(id, tenant_id)
        if doc:
            self.docs.remove(doc)
            return True
        return False


FLOW_TE = {
    "_id": "f1", "tenant_id": "totalelectrique", "name": "Devis Borne", "slug": "devis-borne",
    "status": "published", "version": 1,
    "nodes": [
        {"id": "start", "type": "start", "data": {}},
        {"id": "end1", "type": "end", "data": {"endType": "thank_you"}},
    ],
    "edges": [], "created_at": "2026-01-01", "updated_at": "2026-01-01",
}
FLOW_ITV = {
    "_id": "f2", "tenant_id": "itvalley", "name": "Flow ITV", "slug": "flow-itv",
    "status": "published", "version": 1,
    "nodes": [{"id": "start", "type": "start", "data": {}}],
    "edges": [], "created_at": "2026-01-01", "updated_at": "2026-01-01",
}


@pytest.mark.asyncio
async def test_list_flows_filtra_por_tenant():
    service = FlowService()
    fake = FakeFlowRepository([FLOW_TE.copy(), FLOW_ITV.copy()])
    service._repository = fake

    result = await service.list_all(tenant_id="totalelectrique")
    assert result["total"] == 1
    assert result["flows"][0]["tenant_id"] == "totalelectrique"
    assert ("find_all", "totalelectrique") in fake.calls


@pytest.mark.asyncio
async def test_get_flow_de_outro_tenant_retorna_none():
    service = FlowService()
    service._repository = FakeFlowRepository([FLOW_ITV.copy()])

    result = await service.get_by_id("f2", tenant_id="totalelectrique")
    assert result is None


@pytest.mark.asyncio
async def test_create_flow_carimba_tenant_do_jwt():
    service = FlowService()
    fake = FakeFlowRepository([])
    service._repository = fake

    data = {
        "name": "Novo Flow",
        "nodes": [{"id": "start", "type": "start", "data": {}}],
        "edges": [],
        # cliente tenta forjar outro tenant — deve ser sobrescrito
        "tenant_id": "hacker",
    }
    result = await service.create(data, tenant_id="itvalley")
    assert result["tenant_id"] == "itvalley"
    assert fake.docs[0]["tenant_id"] == "itvalley"


@pytest.mark.asyncio
async def test_delete_flow_escopado_ao_tenant():
    service = FlowService()
    fake = FakeFlowRepository([FLOW_TE.copy()])
    service._repository = fake

    # outro tenant nao consegue deletar
    assert await service.delete("f1", tenant_id="itvalley") is False
    # dono consegue
    assert await service.delete("f1", tenant_id="totalelectrique") is True


@pytest.mark.asyncio
async def test_submission_publica_resolve_tenant_pelo_flow():
    """Submission publica: tenant NUNCA vem do cliente — sai do doc do flow."""
    service = SubmissionService()
    service._flow_repository = FakeFlowRepository([FLOW_TE.copy()])
    fake_subs = FakeSubmissionRepository()
    service._repository = fake_subs

    data = {
        "flow_id": "f1",
        "flow_slug": "devis-borne",
        "client_name": "Client Final",
        "client_email": "client@x.com",
        "answers": [],
        "end_node_id": "end1",
        # cliente tenta forjar outro tenant — deve ser ignorado
        "tenant_id": "hacker",
    }
    result = await service.create(data)
    assert fake_subs.inserted["tenant_id"] == "totalelectrique"
    assert result["tenant_id"] == "totalelectrique"


@pytest.mark.asyncio
async def test_submission_publica_flow_inexistente_da_erro():
    service = SubmissionService()
    service._flow_repository = FakeFlowRepository([])
    with pytest.raises(ValueError):
        await service.create({
            "flow_id": "nao-existe", "flow_slug": "x",
            "client_name": "A", "client_email": "a@x.com",
            "answers": [], "end_node_id": "end1",
        })


@pytest.mark.asyncio
async def test_list_submissions_filtra_por_tenant():
    service = SubmissionService()
    fake = FakeSubmissionRepository([
        {"_id": "s1", "tenant_id": "totalelectrique", "flow_id": "f1"},
        {"_id": "s2", "tenant_id": "itvalley", "flow_id": "f2"},
    ])
    service._repository = fake

    result = await service.list_all(tenant_id="itvalley")
    assert result["total"] == 1
    assert result["submissions"][0]["tenant_id"] == "itvalley"
    assert ("find_all", "itvalley") in fake.calls
