"""Orquestrador publico da geracao de orcamentos.

Responsabilidades:
  - Montar QuoteDeps a partir dos dados da requisicao
  - Delegar execucao ao agente PydanticAI (via AgentService)
  - Formatar saida como texto legivel (quote_text) e estruturado (quote_data)
  - Fornecer fallback sem IA em caso de erro de conexao
"""

import logging

from models.quote_deps import QuoteDeps
from schemas.quote import QuoteOutput
from services.agent_service import get_model_name, get_or_build_agent

logger = logging.getLogger(__name__)


def format_quote_text(output: QuoteOutput, client_name: str) -> str:
    """Formata o QuoteOutput como texto legivel para o cliente final."""
    lines = [
        "=" * 50,
        "       DEVIS ESTIMATIF",
        "       Total Electrique",
        "=" * 50,
        f"\nClient: {client_name}\n",
        "-" * 50,
    ]

    for item in output.items:
        qty_str = f" x{item.quantity}" if item.quantity > 1 else ""
        lines.append(f"  {item.description}{qty_str}")
        lines.append(f"    ${item.subtotal:,.2f}")

    lines += [
        "-" * 50,
        f"  Sous-total:     ${output.subtotal:,.2f}",
        f"  TPS (5%):       ${output.taxes_tps:,.2f}",
        f"  TVQ (9.975%):   ${output.taxes_tvq:,.2f}",
        f"  TOTAL:          ${output.total:,.2f}",
        "-" * 50,
    ]

    if output.recommendations:
        lines.append(f"\nRecommandations:\n{output.recommendations}")
    if output.notes:
        lines.append(f"\nNotes:\n{output.notes}")

    lines += [
        "\n" + "=" * 50,
        "Validite: 30 jours",
        "Inspection pre-installation gratuite",
        "Garantie 2 ans main d'oeuvre",
        "Permis municipal inclus",
        "=" * 50,
    ]

    return "\n".join(lines)


class QuoteService:
    """Interface publica — chamada pelo SubmissionService."""

    @staticmethod
    async def generate(
        business_context: str,
        client_data: dict,
        answers: list[dict],
        ai_instruction: str = "",
        pricing_csv: str = "",
        catalog_map: dict | None = None,
    ) -> dict:
        """Gera orcamento usando PydanticAI com output estruturado.

        Retorna dict com 'quote_text' (formatado) e 'quote_data' (estruturado).
        """
        deps = QuoteDeps(
            pricing_csv=pricing_csv,
            answers=answers,
            business_rules=business_context,
            ai_instruction=ai_instruction,
            client_name=client_data.get("client_name", ""),
            client_email=client_data.get("client_email", ""),
            client_phone=client_data.get("client_phone", ""),
            client_address=client_data.get("client_address", ""),
            catalog_map=catalog_map or {},
        )

        try:
            model_name = await get_model_name()
            agent = get_or_build_agent(model_name)
            result = await agent.run(
                "Genere le devis complet base sur les reponses du client et le catalogue de prix.",
                deps=deps,
            )

            quote_output: QuoteOutput = result.output
            logger.info(f"Devis genere: {len(quote_output.items)} items, total=${quote_output.total}")

            return {
                "quote_text": format_quote_text(quote_output, deps.client_name),
                "quote_data": {
                    "items": [item.model_dump() for item in quote_output.items],
                    "subtotal": quote_output.subtotal,
                    "taxes_tps": quote_output.taxes_tps,
                    "taxes_tvq": quote_output.taxes_tvq,
                    "total": quote_output.total,
                    "recommendations": quote_output.recommendations,
                    "notes": quote_output.notes,
                },
            }

        except Exception as e:
            logger.error(f"Erreur PydanticAI: {e}")
            return {
                "quote_text": QuoteService._generate_basic(client_data, answers),
                "quote_data": None,
            }

    @staticmethod
    def _generate_basic(client_data: dict, answers: list[dict]) -> str:
        """Fallback sem IA — lista as respostas."""
        client_text = (
            f"Nom: {client_data.get('client_name', '')}\n"
            f"Email: {client_data.get('client_email', '')}\n"
            f"Tel: {client_data.get('client_phone', 'N/A')}\n"
            f"Adresse: {client_data.get('client_address', 'N/A')}"
        )
        answers_text = "\n".join(
            f"- {a.get('question', '?')}: {a.get('value', '')}" for a in answers
        )
        return (
            "=" * 50 + "\n"
            "       DEVIS ESTIMATIF\n"
            "       Total Electrique\n"
            + "=" * 50 + "\n"
            f"\n{client_text}\n\n"
            "Reponses:\n"
            f"{answers_text}\n\n"
            "NOTE: Devis genere sans IA (erreur de connexion).\n"
            "Un specialiste vous contactera pour le devis detaille.\n"
            + "=" * 50
        )
