from typing import Optional
from data.repositories.mongo.submission_repository import SubmissionRepository
from data.repositories.mongo.flow_repository import FlowRepository
from factories.submission_factory import SubmissionFactory
from mappers.submission_mapper import SubmissionMapper
from services.quote_service import QuoteService


class SubmissionService:
    """Camada opaca — orquestra Factory, Repository, Mapper e QuoteService."""

    def __init__(self):
        self._repository = SubmissionRepository()
        self._flow_repository = FlowRepository()
        self._factory = SubmissionFactory
        self._mapper = SubmissionMapper
        self._quote_generator = QuoteService

    async def list_all(self) -> dict:
        docs = await self._repository.find_all()
        summaries = [self._mapper.to_summary(doc) for doc in docs]
        return {"submissions": summaries, "total": len(summaries)}

    async def list_by_flow(self, flow_id: str) -> dict:
        docs = await self._repository.find_by_flow(flow_id)
        summaries = [self._mapper.to_summary(doc) for doc in docs]
        return {"submissions": summaries, "total": len(summaries)}

    async def get_by_id(self, id: str) -> Optional[dict]:
        doc = await self._repository.find_by_id(id)
        if not doc:
            return None
        return self._mapper.to_response(doc)

    async def create(self, data: dict) -> dict:
        # Buscar flow para pegar o end_node com businessContext
        flow_doc = await self._flow_repository.find_by_id(data["flow_id"])
        if not flow_doc:
            raise ValueError("Flow nao encontrado")

        # Encontrar o end_node
        end_node = None
        for node in flow_doc.get("nodes", []):
            if node.get("id") == data["end_node_id"]:
                end_node = node
                break

        if not end_node:
            raise ValueError("No final nao encontrado no flow")

        # Pegar pricing_csv do flow
        pricing_csv = flow_doc.get("pricing_csv", "")

        # Montar mapa node_id → catalogProduct a partir dos nós do flow.
        # Quando o admin vincula uma opção a um produto do CSV no builder,
        # esse mapeamento é usado para match determinístico (sem depender da IA).
        catalog_map = _build_catalog_map(flow_doc.get("nodes", []))

        # Criar submission via Factory
        submission_doc = self._factory.create_new(data, end_node)

        # Se o end_type for quote, gerar orcamento
        if submission_doc["end_type"] == "quote":
            quote_result = await self._quote_generator.generate(
                business_context=submission_doc.get("business_context", ""),
                ai_instruction=submission_doc.get("ai_instruction", ""),
                client_data=data,
                answers=data["answers"],
                pricing_csv=pricing_csv,
                catalog_map=catalog_map,
            )
            submission_doc["quote_text"] = quote_result["quote_text"]
            submission_doc["quote_data"] = quote_result["quote_data"]
            submission_doc["status"] = "quoted"

        # Salvar
        saved = await self._repository.insert(submission_doc)
        return self._mapper.to_response(saved)

    async def delete(self, id: str) -> bool:
        return await self._repository.delete(id)

    async def export(self, id: str) -> Optional[dict]:
        """Gera texto do devis, salva .txt e .json localmente, retorna conteudo e caminho."""
        import os
        import json
        from datetime import datetime, timezone

        doc = await self._repository.find_by_id(id)
        if not doc:
            return None

        result = self._mapper.to_response(doc)

        exports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports")
        os.makedirs(exports_dir, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        slug = result.get("flow_slug", "unknown")
        client = result.get("client_name", "unknown").replace(" ", "_")
        filename = f"devis_{slug}_{client}_{timestamp}.txt"
        filepath = os.path.join(exports_dir, filename)

        content = f"DEVIS - {result.get('flow_slug', '')}\n"
        content += f"Date: {result.get('created_at', '')}\n"
        content += f"Client: {result.get('client_name', '')}\n"
        content += f"Email: {result.get('client_email', '')}\n"
        content += f"Tel: {result.get('client_phone', 'N/A')}\n"
        content += f"Adresse: {result.get('client_address', 'N/A')}\n\n"
        content += "--- REPONSES ---\n"
        for a in result.get("answers", []):
            content += f"- {a.get('question', '')}: {a.get('value', '')}\n"
        content += "\n--- DEVIS ---\n"
        content += result.get("quote_text", "Aucun devis genere") + "\n"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        json_path = filepath.replace(".txt", ".json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return {"content": content, "filename": filename, "filepath": filepath}


def _build_catalog_map(nodes: list) -> dict[str, str]:
    """Constrói mapa { answer_value → catalogProduct } a partir dos nós do flow.

    Percorre todos os nós de pergunta com opções e, para cada opção que tem
    catalogProduct definido pelo admin, registra a associação.
    O match é feito pelo campo `value` da opção (o que é salvo nas respostas).
    """
    catalog_map: dict[str, str] = {}
    for node in nodes:
        data = node.get("data", {})
        options = data.get("options", [])
        for opt in options:
            catalog_product = opt.get("catalogProduct", "").strip()
            value = opt.get("value", "").strip()
            if catalog_product and value:
                catalog_map[value.lower()] = catalog_product
            # Também indexa pelo label, para cobrir casos onde o frontend salva o label como value
            label = opt.get("label", "").strip()
            if catalog_product and label and label.lower() not in catalog_map:
                catalog_map[label.lower()] = catalog_product
    return catalog_map
