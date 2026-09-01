"""Cria/atualiza um usuario do auth local (AUTH_LOCAL=true).

Uso:
  MONGODB_URI=... MONGODB_DATABASE=flowquote python scripts/create_local_user.py \
    --email hugo@... --password ... --name "Hugo" --tenant totalelectrique
"""
import argparse
import hashlib
import os
import secrets

import certifi
from pymongo import MongoClient

PBKDF2_ITERS = 120_000

ap = argparse.ArgumentParser()
ap.add_argument("--email", required=True)
ap.add_argument("--password", required=True)
ap.add_argument("--name", required=True)
ap.add_argument("--tenant", required=True)
ap.add_argument("--master", action="store_true")
a = ap.parse_args()

salt = secrets.token_hex(16)
h = hashlib.pbkdf2_hmac("sha256", a.password.encode(), bytes.fromhex(salt), PBKDF2_ITERS).hex()

c = MongoClient(os.environ["MONGODB_URI"], tlsCAFile=certifi.where())
db = c[os.environ.get("MONGODB_DATABASE", "flowquote")]
db["users"].update_one(
    {"email": a.email.strip().lower()},
    {"$set": {
        "email": a.email.strip().lower(), "name": a.name, "tenant_id": a.tenant,
        "password_salt": salt, "password_hash": h, "active": True,
        "is_master": a.master, "products": ["quanto"], "permissions": {},
    }},
    upsert=True,
)
print(f"ok: {a.email} (tenant={a.tenant})")
