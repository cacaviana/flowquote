"""Agente de orcamento com PydanticAI.

Recebe o CSV de precos + respostas do formulario e gera um orcamento
estruturado com output parsing. O CSV evita alucinacao de precos.
"""

import csv
import io
import logging
from dataclasses import dataclass

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from config.settings import settings

logger = logging.getLogger(__name__)


# ── Output estruturado (o que o agente retorna) ──


class QuoteItem(BaseModel):
    """Um item do orcamento."""

    description: str = Field(description="Nom du produit ou service")
    unit_price: float = Field(description="Prix unitaire du catalogue CSV")
    quantity: int = Field(default=1, description="Quantite")
    subtotal: float = Field(description="unit_price * quantity")


class QuoteOutput(BaseModel):
    """Orcamento completo gerado pelo agente."""

    items: list[QuoteItem] = Field(description="Lignes du devis")
    subtotal: float = Field(description="Somme des items")
    taxes_tps: float = Field(description="TPS 5%")
    taxes_tvq: float = Field(description="TVQ 9.975%")
    total: float = Field(description="Total final TTC")
    recommendations: str = Field(
        description="Recommandations techniques basees sur les reponses"
    )
    notes: str = Field(
        default="",
        description="Notes additionnelles (subventions, conditions)",
    )


# ── Dependencias injetadas no agente ──


@dataclass
class QuoteDeps:
    pricing_csv: str  # CSV bruto do tenant
    answers: list[dict]  # Respostas do formulario
    business_rules: str  # businessContext do EndNode
    ai_instruction: str  # aiInstruction do EndNode
    client_name: str
    client_email: str
    client_phone: str
    client_address: str
    catalog_map: dict  # { answer_value_lower → catalogProduct } — mapeamento determinístico do admin


# ── Modelo da IA ──


def _get_model_name() -> str:
    provider = settings.ai_provider.lower()
    if provider == "anthropic" and settings.anthropic_api_key:
        return f"anthropic:{settings.anthropic_model}"
    if settings.openai_api_key:
        return f"openai:{settings.openai_model}"
    raise ValueError("Nenhuma API key configurada (OPENAI_API_KEY ou ANTHROPIC_API_KEY)")


def _setup_env():
    """Garante que as env vars estejam setadas para o PydanticAI."""
    import os
    if settings.openai_api_key and not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key
    if settings.anthropic_api_key and not os.environ.get("ANTHROPIC_API_KEY"):
        os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key


_setup_env()


# ── Agente PydanticAI ──

quote_agent = Agent(
    model=_get_model_name(),
    deps_type=QuoteDeps,
    output_type=QuoteOutput,
    instructions="""## Papel
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
- Montants en dollars canadiens.""",
)


@quote_agent.system_prompt
def build_context(ctx: RunContext[QuoteDeps]) -> str:
    """Injecte le contexte complet dans le prompt systeme."""
    csv_table = _format_csv_for_prompt(ctx.deps.pricing_csv)

    # Classifica cada resposta em: produto confirmado, produto ausente, ou contexto puro.
    # Prioridade 1: admin mapeou explicitamente via catalogProduct no builder.
    # Prioridade 2: auto-detecção por match exato do value com o CSV.
    # O que não se encaixa em nenhum dos dois → contexto puro (região, amperagem, etc.).
    catalog = _parse_csv_catalog(ctx.deps.pricing_csv)

    confirmed: list[str] = []   # produtos com preço confirmado
    absent: list[str] = []      # produtos mapeados mas ausentes do CSV
    context_answers: list[str] = []  # respostas que são contexto, não produto

    for answer in ctx.deps.answers:
        value = str(answer.get("value", "")).strip()
        question = answer.get("question", answer.get("node_id", "?"))

        # Prioridade 1: admin mapeou esta opção explicitamente
        admin_product = ctx.deps.catalog_map.get(value.lower(), "")
        if admin_product:
            if catalog:
                match = _find_catalog_match(admin_product, catalog)
                if match:
                    confirmed.append(f"  - {admin_product} @ ${match['price']} (cliente escolheu \"{value}\")")
                else:
                    absent.append(f"  - \"{value}\" → \"{admin_product}\" ausente do CSV → preco 0 + \"(prix a consulter)\"")
            else:
                absent.append(f"  - \"{value}\" → \"{admin_product}\" (sem CSV carregado) → preco 0 + \"(prix a consulter)\"")
            continue

        # Prioridade 2: auto-detecção por match exato
        if catalog:
            exact = next(
                (p for p in catalog if p["name"] == value.lower() or p["name_original"] == value),
                None,
            )
            if exact:
                confirmed.append(f"  - {exact['name_original']} @ ${exact['price']} (auto-detectado de \"{value}\")")
                continue

        # Sem match → contexto puro
        context_answers.append(f"  - {question}: {value}")

    # Monta seções do prompt
    confirmed_section = ""
    if confirmed:
        confirmed_section = (
            "\n\nPRODUTOS SELECIONADOS PELO CLIENTE — confirmados no catalogo:\n"
            "(Copie estes itens NO DEVIS com o preco exato. NAO altere nome nem preco.)\n"
            + "\n".join(confirmed)
        )

    absent_section = ""
    if absent:
        absent_section = (
            "\n\nPRODUTOS SELECIONADOS PELO CLIENTE — AUSENTES do catalogo:\n"
            "(Incluir no devis com preco 0 e sufixo '(prix a consulter)'. NAO substituir por produto similar.)\n"
            + "\n".join(absent)
        )

    other_section = ""
    if context_answers:
        other_section = (
            "\n\nOUTRAS RESPOSTAS DO CLIENTE:\n"
            "(Contexto tecnico — regiao, amperagem, nome, etc. — OU descricoes de servico/produto "
            "que NAO constam exatamente no catalogo.\n"
            "REGRA: Se for relevante ao devis, incluir com a DESCRICAO EXATA do cliente "
            "(INTERDIT de renomear ou substituir pelo nome de um produto do catalogo). "
            "Se nao estiver no catalogo: preco 0 + \"(prix a consulter)\". "
            "INTERDIT de inventar um preco aproximado baseado num produto parecido. "
            "Informacoes pessoais (nome, email, telefone, endereco) NUNCA sao itens.)\n"
            + "\n".join(context_answers)
        )

    prompt = f"""CATALOGUE DE PRIX (source de verite ABSOLUE — unicos produtos e precos autorizados):
{csv_table}{confirmed_section}{absent_section}{other_section}

REGRAS:
1. Os PRODUTOS CONFIRMADOS acima DEVEM estar no devis com o preco exato — nao alterar
2. Preco de qualquer item DEVE ser do catalogo — JAMAIS inventar preco
3. Para produtos por unidade (ex: por pe), multiplicar preco x quantidade
4. Se servico nao tiver preco no catalogo: incluir com preco 0 + "(prix a consulter)"
5. Informacoes pessoais do cliente (nome, email, telefone) NUNCA sao itens do devis

CLIENT:
Nom: {ctx.deps.client_name}
Email: {ctx.deps.client_email}
Tel: {ctx.deps.client_phone or 'N/A'}
Adresse: {ctx.deps.client_address or 'N/A'}"""

    if ctx.deps.business_rules:
        prompt += f"""

REGLES METIER SPECIFIQUES:
{ctx.deps.business_rules}"""

    if ctx.deps.ai_instruction:
        prompt += f"""

INSTRUCTIONS DE FORMAT:
{ctx.deps.ai_instruction}"""

    return prompt


def _build_client_mentions(answers: list[dict], catalog_map: dict) -> set[str]:
    """Constrói conjunto de palavras-chave vindas das respostas do cliente.

    Inclui valores das respostas, produtos mapeados pelo admin e palavras
    significativas dos títulos das perguntas.
    Usado pelo validador para distinguir itens solicitados pelo cliente de
    itens adicionados por iniciativa da IA (esses ficam com quantity=1).
    """
    mentioned: set[str] = set()
    for answer in answers:
        value = str(answer.get("value", "")).strip()
        question = str(answer.get("question", "")).strip()
        # Admin-mapped option
        admin_product = catalog_map.get(value.lower(), "")
        if admin_product:
            mentioned.add(admin_product.lower())
        # Raw answer value
        mentioned.add(value.lower())
        # Significant words from the question label (e.g. "cabeamento" from
        # "Metragem de cabeamento" links to "Cabeamento por metro")
        for word in question.lower().split():
            if len(word) > 4:
                mentioned.add(word)
    return mentioned


@quote_agent.output_validator
async def validate_quote(ctx: RunContext[QuoteDeps], output: QuoteOutput) -> QuoteOutput:
    """Valide que les items existent dans le CSV et que les calculs sont corrects."""
    catalog = _parse_csv_catalog(ctx.deps.pricing_csv)
    client_mentions = _build_client_mentions(ctx.deps.answers, ctx.deps.catalog_map)

    if catalog:
        validated_items = []
        for item in output.items:
            match = _find_catalog_match(item.description, catalog)
            if match:
                # Force the unit_price from CSV — no hallucination
                item.unit_price = match["price"]
                # If item was NOT explicitly requested by client, cap quantity at 1
                desc_lower = item.description.lower()
                client_requested = any(
                    mention in desc_lower or desc_lower in mention
                    for mention in client_mentions
                    if mention
                )
                if not client_requested:
                    item.quantity = 1
                item.subtotal = round(match["price"] * item.quantity, 2)
                validated_items.append(item)
            else:
                logger.warning(
                    f"Item hors catalogue: {item.description} @ ${item.unit_price}"
                )
                # Keep the item but mark price as 0 (to consult)
                item.unit_price = 0
                item.quantity = 1
                item.subtotal = 0
                # Avoid duplicate suffix if AI already added it
                if "prix" not in item.description.lower() or "consulter" not in item.description.lower():
                    item.description = f"{item.description} (prix a consulter)"
                validated_items.append(item)

        output.items = validated_items

    # Recalculate subtotals
    for item in output.items:
        expected = round(item.unit_price * item.quantity, 2)
        if abs(item.subtotal - expected) > 0.01:
            item.subtotal = expected

    # Recalculate total
    subtotal = round(sum(i.subtotal for i in output.items), 2)
    output.subtotal = subtotal

    tps = round(subtotal * 0.05, 2)
    tvq = round(subtotal * 0.09975, 2)
    output.taxes_tps = tps
    output.taxes_tvq = tvq
    output.total = round(subtotal + tps + tvq, 2)

    return output


def _parse_csv_catalog(csv_text: str) -> list[dict]:
    """Parse le CSV en liste de produits avec prix."""
    if not csv_text or not csv_text.strip():
        return []

    try:
        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        catalog = []
        for row in reader:
            name = row.get("produto", "").strip()
            price_str = row.get("preco", "0").strip()
            try:
                price = float(price_str)
            except ValueError:
                continue
            if name:
                catalog.append({"name": name.lower(), "name_original": name, "price": price})
        return catalog
    except Exception:
        return []


def _find_catalog_match(item_description: str, catalog: list[dict]) -> dict | None:
    """Trouve le produit du catalogue qui correspond le mieux a la description.

    Utilise une correspondance flexible pour gerer les variations de noms
    que l'IA peut generer (ex: 'Borne 32A Level 2' vs 'Borne 32A').
    """
    desc_lower = item_description.lower()

    # Exact match
    for product in catalog:
        if product["name"] == desc_lower or product["name_original"].lower() == desc_lower:
            return product

    # Partial match: catalog name is fully contained in the description or vice-versa
    best_match = None
    best_len = 0
    for product in catalog:
        if product["name"] in desc_lower or desc_lower in product["name"]:
            if len(product["name"]) > best_len:
                best_match = product
                best_len = len(product["name"])

    # Keyword match: ALL meaningful words from the catalog must appear in the description.
    # This prevents "installation murale intérieure" from matching "installation murale extérieure"
    # because "extérieure" would be absent from the description.
    # Tokens are "meaningful" if they are long words (>3 chars) OR contain digits (model codes
    # like "4mp", "8mp", "4k", "32a" etc. that discriminate between products).
    # IMPORTANT: requires at least 2 meaningful words — a single generic word like "mobile"
    # or "camera" is not specific enough to confirm a match.
    if not best_match:
        for product in catalog:
            prod_words = set(product["name"].split())
            desc_words = set(desc_lower.split())
            meaningful_prod_words = {
                w for w in prod_words
                if len(w) > 3 or (len(w) >= 2 and any(c.isdigit() for c in w))
            }
            if len(meaningful_prod_words) < 2:
                continue
            # Every meaningful word of the catalog product must be in the description
            if meaningful_prod_words.issubset(desc_words):
                if not best_match or len(meaningful_prod_words) > best_len:
                    best_match = product
                    best_len = len(meaningful_prod_words)

    return best_match


def _format_csv_for_prompt(csv_text: str) -> str:
    """Formata o CSV como tabela legivel para o prompt."""
    if not csv_text.strip():
        return "(Aucun catalogue de prix fourni)"

    try:
        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        lines = []
        for row in reader:
            produto = row.get("produto", "").strip()
            preco = row.get("preco", "0").strip()
            unidade = row.get("unidade", "").strip()
            categoria = row.get("categoria", "").strip()
            lines.append(f"| {produto} | ${preco} | {unidade} | {categoria} |")

        if not lines:
            return "(CSV vide ou format invalide)"

        header = "| Produit | Prix | Unite | Categorie |"
        separator = "|---------|------|-------|-----------|"
        return "\n".join([header, separator] + lines)

    except Exception as e:
        logger.warning(f"Erro ao parsear CSV: {e}")
        return csv_text  # fallback: envia o texto bruto


def _format_quote_text(output: QuoteOutput, client_name: str) -> str:
    """Formata o QuoteOutput como texto legivel para o cliente final."""
    lines = []
    lines.append("=" * 50)
    lines.append("       DEVIS ESTIMATIF")
    lines.append("       Total Electrique")
    lines.append("=" * 50)
    lines.append(f"\nClient: {client_name}\n")
    lines.append("-" * 50)

    for item in output.items:
        qty_str = f" x{item.quantity}" if item.quantity > 1 else ""
        lines.append(f"  {item.description}{qty_str}")
        lines.append(f"    ${item.subtotal:,.2f}")

    lines.append("-" * 50)
    lines.append(f"  Sous-total:     ${output.subtotal:,.2f}")
    lines.append(f"  TPS (5%):       ${output.taxes_tps:,.2f}")
    lines.append(f"  TVQ (9.975%):   ${output.taxes_tvq:,.2f}")
    lines.append(f"  TOTAL:          ${output.total:,.2f}")
    lines.append("-" * 50)

    if output.recommendations:
        lines.append(f"\nRecommandations:\n{output.recommendations}")

    if output.notes:
        lines.append(f"\nNotes:\n{output.notes}")

    lines.append("\n" + "=" * 50)
    lines.append("Validite: 30 jours")
    lines.append("Inspection pre-installation gratuite")
    lines.append("Garantie 2 ans main d'oeuvre")
    lines.append("Permis municipal inclus")
    lines.append("=" * 50)

    return "\n".join(lines)


class QuoteGenerator:
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
            result = await quote_agent.run(
                "Genere le devis complet base sur les reponses du client et le catalogue de prix.",
                deps=deps,
            )

            quote_output: QuoteOutput = result.output
            logger.info(
                f"Devis genere: {len(quote_output.items)} items, total=${quote_output.total}"
            )

            return {
                "quote_text": _format_quote_text(quote_output, deps.client_name),
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
                "quote_text": QuoteGenerator._generate_basic(client_data, answers),
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
