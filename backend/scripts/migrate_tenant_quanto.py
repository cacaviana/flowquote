"""Migracao multitenant Petra Suite — produto Quanto (FlowQuote).

Regra de marcacao (confirmada em 23/07/2026 nos appsettings dos webapps):
  - database `flowquote`           -> usado pelo TE v1 em producao -> tenant 'totalelectrique'
  - database `flowquote-itvalley`  -> usado pelo FlowQuote novo    -> tenant 'itvalley'

Em TODAS as colecoes do database alvo, documentos com tenant_id ausente,
nulo ou igual a 'tenant_1' (placeholder antigo) recebem o tenant do database.
A marcacao e ADITIVA ($set) — o codigo v1 do TE ignora campos extras.

Uso:
    # dry-run (default): so imprime contagens por colecao, nada e alterado
    MONGODB_URI=... python scripts/migrate_tenant_quanto.py --database flowquote --dry-run
    MONGODB_URI=... python scripts/migrate_tenant_quanto.py --database flowquote-itvalley --dry-run

    # aplicar de verdade
    MONGODB_URI=... python scripts/migrate_tenant_quanto.py --database flowquote --apply

Nunca imprime a URI nem credenciais.
"""
import argparse
import asyncio
import os
import sys

import certifi
from motor.motor_asyncio import AsyncIOMotorClient

TENANT_BY_DATABASE = {
    "flowquote": "totalelectrique",
    "flowquote-itvalley": "itvalley",
}

FILTER = {"$or": [
    {"tenant_id": {"$exists": False}},
    {"tenant_id": None},
    {"tenant_id": "tenant_1"},
]}


async def run(database: str, apply: bool) -> None:
    uri = os.environ.get("MONGODB_URI")
    if not uri:
        print("ERRO: defina MONGODB_URI no ambiente (nao passe por argumento).")
        sys.exit(1)

    tenant = TENANT_BY_DATABASE.get(database)
    if not tenant:
        print(f"ERRO: database '{database}' nao mapeado. Validos: {sorted(TENANT_BY_DATABASE)}")
        sys.exit(1)

    client = AsyncIOMotorClient(uri, tlsCAFile=certifi.where())
    db = client[database]
    collections = sorted(await db.list_collection_names())

    mode = "APPLY" if apply else "DRY-RUN"
    print(f"[{mode}] database={database} -> tenant_id='{tenant}'")
    print(f"{'colecao':30} {'total':>8} {'a_migrar':>10} {'migrados':>10}")

    grand_total = grand_todo = grand_done = 0
    for name in collections:
        col = db[name]
        total = await col.count_documents({})
        todo = await col.count_documents(FILTER)
        done = 0
        if apply and todo:
            result = await col.update_many(FILTER, {"$set": {"tenant_id": tenant}})
            done = result.modified_count
        print(f"{name:30} {total:>8} {todo:>10} {done if apply else '-':>10}")
        grand_total += total
        grand_todo += todo
        grand_done += done

    print(f"{'TOTAL':30} {grand_total:>8} {grand_todo:>10} {grand_done if apply else '-':>10}")
    if not apply:
        print("\nNada foi alterado (dry-run). Use --apply para executar.")
    client.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Marca tenant_id por database (flowquote->totalelectrique, flowquote-itvalley->itvalley)"
    )
    parser.add_argument("--database", required=True, help="Nome do database Mongo")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", help="Somente contagens (default)")
    group.add_argument("--apply", action="store_true", help="Executa de verdade")
    args = parser.parse_args()
    asyncio.run(run(args.database, args.apply))


if __name__ == "__main__":
    main()
