import re
from datetime import datetime, timezone


class FlowFactory:
    """Cria documentos de flow com regras de negocio.

    Responsabilidades:
    - Gerar slug a partir do nome
    - Definir valores default (version, status, timestamps)
    - Validar invariantes (max nodes, start node obrigatorio)
    """

    MAX_NODES = 50

    @staticmethod
    def _generate_slug(name: str) -> str:
        slug = name.lower().strip()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @classmethod
    def _validate_common(cls, nodes: list) -> None:
        if len(nodes) > cls.MAX_NODES:
            raise ValueError(f"Flow nao pode ter mais de {cls.MAX_NODES} nos")
        has_start = any(n.get("type") == "start" for n in nodes)
        if not has_start:
            raise ValueError("Flow precisa ter pelo menos um no de inicio (start)")

    @classmethod
    def _validate_module(cls, module: str, nodes: list, has_csv: bool) -> None:
        """Validacoes especificas por modulo."""
        end_nodes = [n for n in nodes if n.get("type") == "end"]
        if module == "agendamento":
            for en in end_nodes:
                et = en.get("data", {}).get("endType", "")
                if et == "quote":
                    raise ValueError("Modulo agendamento nao suporta endType 'quote'. Use 'booking' ou 'specialist'.")

    @classmethod
    def create_new(cls, data: dict) -> dict:
        nodes = data.get("nodes", [])
        module = data.get("module", "devis")

        cls._validate_common(nodes)
        cls._validate_module(module, nodes, bool(data.get("pricing_csv")))

        now = cls._now_iso()
        slug = data.get("slug") or cls._generate_slug(data["name"])

        doc = {
            "tenant_id": data.get("tenant_id", "tenant_1"),
            "module": module,
            "name": data["name"],
            "slug": slug,
            "status": data.get("status", "draft"),
            "version": 1,
            "nodes": nodes,
            "edges": data.get("edges", []),
            "created_at": now,
            "updated_at": now,
        }
        # pricing_csv so faz sentido no modulo devis
        if module == "devis" and data.get("pricing_csv") is not None:
            doc["pricing_csv"] = data["pricing_csv"]
        return doc

    @classmethod
    def create_update(cls, existing: dict, data: dict) -> dict:
        nodes = data.get("nodes", existing.get("nodes", []))
        module = data.get("module", existing.get("module", "devis"))

        cls._validate_common(nodes)
        cls._validate_module(module, nodes, bool(data.get("pricing_csv") or existing.get("pricing_csv")))

        slug = data.get("slug") or cls._generate_slug(data["name"])

        update_doc = {
            "module": module,
            "name": data["name"],
            "slug": slug,
            "status": data.get("status", existing.get("status", "draft")),
            "version": existing.get("version", 0) + 1,
            "nodes": nodes,
            "edges": data.get("edges", existing.get("edges", [])),
            "updated_at": cls._now_iso(),
        }
        # pricing_csv so faz sentido no modulo devis
        if module == "devis":
            if data.get("pricing_csv") is not None:
                update_doc["pricing_csv"] = data["pricing_csv"]
            elif existing.get("pricing_csv"):
                update_doc["pricing_csv"] = existing["pricing_csv"]
        return update_doc
