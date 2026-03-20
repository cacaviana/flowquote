"""Configuracao e cache do agente PydanticAI.

Responsabilidades:
  - Inicializar env vars para o PydanticAI (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)
  - Resolver o nome do modelo (DB tem prioridade sobre .env)
  - Manter cache de agentes por modelo (evita rebuild desnecessario)
  - Construir agente com system_prompt e output_validator registrados
"""

import logging

from pydantic_ai import Agent

from config.settings import settings
from models.quote_deps import QuoteDeps
from schemas.quote import QuoteOutput

logger = logging.getLogger(__name__)

AGENT_INSTRUCTIONS = """## Papel
Tu es un assistant de devis professionnel pour des entreprises de services.

## Regras absolutas — precos
- Utiliser UNIQUEMENT les prix du catalogue CSV. INTERDIT d'inventer ou approximer un prix.
- INTERDIT d'ajouter subventions, rabais ou deductions absents du CSV.
- Pour tout produit/metrage: prix unitaire CSV x quantite exacte du client.
- INTERDIT de modifier la quantite donnee par le client.

## Regras absolutas — nomes de produtos
- Si un produit client N'EXISTE PAS dans le catalogue: inclure avec la description EXACTE du client, prix 0, suffixe "(prix a consulter)".
- INTERDIT de renommer ou substituer par un produit similaire du catalogue.
- INTERDIT de changer "interieur/exterieur", "plafond/murale", "embutido/externo" ou toute variation de localisation.

## Sugestoes complementares (opcional)
- Tu PEUX ajouter des produits complementaires du catalogue non demandes par le client.
- Ces produits supplementaires: quantite = 1 uniquement, jamais plus.

## Calcul
- TPS 5% + TVQ 9,975% sur le sous-total.
- Montants en dollars canadiens."""

_agent_cache: dict[str, Agent] = {}


def setup_env() -> None:
    """Garante que as env vars estejam setadas para o PydanticAI."""
    import os
    if settings.openai_api_key and not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key
    if settings.openai_base_url and not os.environ.get("OPENAI_BASE_URL"):
        os.environ["OPENAI_BASE_URL"] = settings.openai_base_url
    if settings.anthropic_api_key and not os.environ.get("ANTHROPIC_API_KEY"):
        os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key


setup_env()


async def get_model_name() -> str:
    """Busca modelo do DB (prioridade) ou cai no .env."""
    from services.settings_service import SettingsService
    try:
        cfg = await SettingsService().get_ai_config()
        provider = cfg["provider"]
        model = cfg["model"]
    except Exception:
        provider = settings.ai_provider.lower()
        model = settings.anthropic_model if provider == "anthropic" else settings.openai_model

    if provider == "anthropic" and settings.anthropic_api_key:
        return f"anthropic:{model}"
    if settings.openai_api_key:
        import os
        os.environ.pop("OPENAI_BASE_URL", None)
        return f"openai:{model}"
    raise ValueError("Nenhuma API key configurada")


def get_or_build_agent(model_name: str) -> Agent:
    """Retorna agente do cache ou constroi novo para o modelo dado."""
    if model_name in _agent_cache:
        return _agent_cache[model_name]

    from services.prompt_service import build_context
    from services.validator_service import validate_quote

    agent: Agent = Agent(
        model=model_name,
        deps_type=QuoteDeps,
        output_type=QuoteOutput,
        instructions=AGENT_INSTRUCTIONS,
    )
    agent.system_prompt(build_context)
    agent.output_validator(validate_quote)
    _agent_cache[model_name] = agent
    return agent
