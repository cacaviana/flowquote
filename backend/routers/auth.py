"""Login do Quanto — proxy fino para a identidade central da Petra Suite,
com fallback LOCAL (AUTH_LOCAL=true) enquanto a plataforma nao esta no ar.

Local: autentica contra a colecao `users` (pbkdf2-sha256) e emite o MESMO
par de JWT via itvalleysecurity (claims tenant_id/is_master/products/permissions),
entao require_access e o tenant context funcionam identicos nos dois modos.
"""
import hashlib
import hmac
import logging

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from config.settings import settings
from config.database import mongodb_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

PBKDF2_ITERS = 120_000


class LoginRequest(BaseModel):
    email: str
    password: str


def _hash(password: str, salt_hex: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt_hex), PBKDF2_ITERS
    ).hex()


async def _login_local(body: LoginRequest) -> JSONResponse:
    from itvalleysecurity.core import issue_pair

    db = mongodb_client.client[settings.mongodb_database]
    user = await db["users"].find_one({"email": body.email.strip().lower()})
    if not user or not user.get("active", True):
        raise HTTPException(status_code=401, detail="Email ou senha invalidos")
    salt = user.get("password_salt")
    if not salt or not hmac.compare_digest(
        _hash(body.password, salt), user.get("password_hash") or ""
    ):
        raise HTTPException(status_code=401, detail="Email ou senha invalidos")

    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Usuario sem tenant configurado")
    is_master = bool(user.get("is_master", False))
    products = user.get("products") or ["quanto"]
    permissions = user.get("permissions") or {}

    pair = issue_pair(
        str(user["_id"]),
        email=user["email"],
        tenant_id=tenant_id,
        is_master=is_master,
        products=products,
        permissions=permissions,
    )
    pair = dict(pair)
    return JSONResponse(
        status_code=200,
        content={
            "access_token": pair.get("access_token"),
            "refresh_token": pair.get("refresh_token"),
            "token_type": "bearer",
            "user": {
                "id": str(user["_id"]),
                "name": user.get("name") or user["email"],
                "email": user["email"],
            },
            "tenant": {"id": tenant_id, "slug": tenant_id, "is_master": is_master},
            "products": [{"slug": p} for p in products],
        },
    )


@router.post("/login")
async def login(body: LoginRequest):
    """Autentica local (AUTH_LOCAL=true) ou via plataforma Petra Suite (proxy)."""
    if settings.auth_local:
        return await _login_local(body)

    url = f"{settings.platform_auth_url.rstrip('/')}/api/auth/login"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                url,
                json={"email": body.email, "password": body.password},
            )
    except httpx.HTTPError as e:
        logger.error(f"Erro ao contatar a plataforma de identidade: {e}")
        raise HTTPException(
            status_code=502,
            detail="Servico de autenticacao indisponivel. Tente novamente.",
        )

    try:
        data = resp.json()
    except ValueError:
        logger.error(f"Resposta nao-JSON da plataforma (status {resp.status_code})")
        raise HTTPException(status_code=502, detail="Resposta invalida do servico de autenticacao")

    return JSONResponse(status_code=resp.status_code, content=data)
