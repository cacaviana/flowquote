from typing import Optional
from data.repositories.mongo.submission_repository import SubmissionRepository
from data.repositories.mongo.flow_repository import FlowRepository
from factories.submission_factory import SubmissionFactory
from mappers.submission_mapper import SubmissionMapper
from services.quote_generator import QuoteGenerator


class SubmissionService:
    """Camada opaca — orquestra Factory, Repository, Mapper e QuoteGenerator."""

    def __init__(self):
        self._repository = SubmissionRepository()
        self._flow_repository = FlowRepository()
        self._factory = SubmissionFactory
        self._mapper = SubmissionMapper
        self._quote_generator = QuoteGenerator

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
