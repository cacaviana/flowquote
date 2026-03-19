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
            )
            submission_doc["quote_text"] = quote_result["quote_text"]
            submission_doc["quote_data"] = quote_result["quote_data"]
            submission_doc["status"] = "quoted"

        # Salvar
        saved = await self._repository.insert(submission_doc)
        return self._mapper.to_response(saved)

    async def delete(self, id: str) -> bool:
        return await self._repository.delete(id)
