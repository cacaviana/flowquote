"""Testes HTTP das rotas — protecao admin e rota publica (sem rede/Mongo)."""
import pytest
from fastapi.testclient import TestClient

from main import app
from itvalleysecurity.fastapi import require_access
import routers.flow as flow_router_module


class FakeFlowRepository:
    def __init__(self, docs):
        self.docs = docs

    async def find_all(self, tenant_id=None):
        return [d for d in self.docs if tenant_id is None or d.get("tenant_id") == tenant_id]

    async def find_by_id(self, id, tenant_id=None):
        for d in self.docs:
            if d["_id"] == id and (tenant_id is None or d.get("tenant_id") == tenant_id):
                return d
        return None

    async def find_by_slug(self, slug, tenant_id=None):
        for d in self.docs:
            if d["slug"] == slug and (tenant_id is None or d.get("tenant_id") == tenant_id):
                return d
        return None


FLOW_TE = {
    "_id": "665f00000000000000000001", "tenant_id": "totalelectrique",
    "name": "Devis Borne", "slug": "devis-borne", "status": "published",
    "version": 1, "nodes": [], "edges": [],
    "created_at": "2026-01-01", "updated_at": "2026-01-01",
}


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def fake_repo(monkeypatch):
    fake = FakeFlowRepository([FLOW_TE])
    monkeypatch.setattr(flow_router_module._service, "_repository", fake)
    yield fake


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


def _override_auth(claims: dict):
    async def fake_require_access():
        return {"sub": "u@x.com", "email": "u@x.com", "claims": claims}
    app.dependency_overrides[require_access] = fake_require_access


def test_admin_sem_token_401(client):
    resp = client.get("/api/flows")
    assert resp.status_code == 401


def test_admin_403_sem_produto_quanto(client):
    _override_auth({"tenant_id": "totalelectrique", "is_master": False, "products": ["calenda"]})
    resp = client.get("/api/flows")
    assert resp.status_code == 403
    assert resp.json()["detail"]["error"] == "ProductNotSubscribed"


def test_admin_lista_flows_do_tenant(client):
    _override_auth({"tenant_id": "totalelectrique", "is_master": False, "products": ["quanto"]})
    resp = client.get("/api/flows")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["flows"][0]["tenant_id"] == "totalelectrique"


def test_rota_publica_slug_sem_auth(client):
    resp = client.get("/api/flows/slug/devis-borne")
    assert resp.status_code == 200
    assert resp.json()["tenant_id"] == "totalelectrique"
