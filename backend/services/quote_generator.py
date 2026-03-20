"""Agente de orcamento com PydanticAI.

PROBLEMA CENTRAL
----------------
LLMs baratos (e às vezes os caros) cometem dois tipos de alucinação de catálogo:
  1. Substituição de nome  — "Camera 4K Ultra HD" vira "Camera IP 8MP" (produto similar presente no CSV)
  2. Substituição de preço — a IA mantém o nome correto mas usa o preço de um produto parecido

ARQUITETURA ANTI-ALUCINAÇÃO — 3 CAMADAS INDEPENDENTES
------------------------------------------------------
As camadas são projetadas para serem complementares: se uma falha (especialmente
em modelos baratos), as outras ainda protegem o resultado.

Camada 1 — PROMPT ESTRUTURADO  (build_context)
    Classifica cada resposta do cliente em três buckets ANTES de enviar à IA:

    • PRODUTOS CONFIRMADOS  — opção mapeada pelo admin (catalogProduct) OU match exato
      do value com o CSV. A IA recebe o nome e o preço correto e deve copiar sem alterar.

    • PRODUTOS AUSENTES     — opção com catalogProduct definido, mas o produto não está no
      CSV. A IA recebe instrução explícita: preço 0 + "(prix a consulter)", sem substituição.

    • OUTRAS RESPOSTAS      — contexto (região, amperagem, nome do cliente) ou seleções cujo
      nome não bate exatamente com o CSV. A IA decide se gera item, mas DEVE usar a descrição
      exata do cliente — INTERDIT de renomear para um produto do catálogo.

    Prompt usa seções com ## para compatibilidade com modelos menores.

Camada 2 — FUZZY MATCH RIGOROSO  (_find_catalog_match)
    Valida se uma string corresponde a algum produto do CSV.
    Ordem: exato → parcial → keyword.

    O keyword match exige:
      • ≥ 2 palavras "significativas" do produto do catálogo (len > 3 ou contém dígito)
      • Todas essas palavras presentes na descrição
    Isso impede que "Camera IP 4MP" bata com "Camera 4K Ultra HD" via
    a palavra genérica "camera" sozinha. Tokens com dígitos (4mp, 32a, 4k)
    são tratados como significativos mesmo tendo ≤ 3 caracteres.

Camada 3 — VALIDADOR PÓS-IA  (validate_quote)
    Código puro — não depende do comportamento do modelo.
    Para cada item que a IA retornou:

    a) Se encontra match no catálogo (via _find_catalog_match):
       • Força unit_price = preço do CSV (elimina alucinação de preço)
       • Se o item NÃO foi solicitado pelo cliente (AI adicionou por conta própria):
         força quantity = 1 (evita quantidades inventadas)

    b) Se NÃO encontra match no catálogo:
       • unit_price = 0, subtotal = 0
       • Adiciona sufixo "(prix a consulter)" se ausente

    c) CONFIRMADOS FORÇADOS — produtos que o sistema classificou como confirmados
       (catalog_map + exact matches) são re-verificados: se a IA os descreveu
       diferente e o validador não os encontrou, são injetados com o preço correto.
       Isso protege contra modelos over-conservative (ex: Haiku) que marcam tudo
       como "A consulter" mesmo quando o produto está confirmado no catálogo.

    Recalcula subtotais, TPS (5%) e TVQ (9,975%) sempre — independente do que a IA calculou.

DADOS DE TESTE
--------------
  Flow: devis-automacao-comercial  — 2 armadilhas (Camera 4K Ultra HD, Instalacao embutida teto)
  Flow: devis-dev-software         — 4 armadilhas (E-commerce avancado, App mobile hibrido,
                                      API GraphQL, SEO avancado)

RESULTADOS POR MODELO (2026-03-20)
-----------------------------------
  claude-sonnet-4  — 100% sem alucinação, itens confirmados precificados corretamente
  claude-haiku-4.5 — 0% substituição de nome/preço, mas over-conservative (marca tudo como
                     A consulter quando há muitos itens ausentes); Camada 3c corrige isso
  gpt-4o-mini      — Falha: substitui nomes e preços, ignora regras do prompt
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


def _setup_env():
    """Garante que as env vars estejam setadas para o PydanticAI."""
    import os
    if settings.openai_api_key and not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key
    if settings.openai_base_url and not os.environ.get("OPENAI_BASE_URL"):
        os.environ["OPENAI_BASE_URL"] = settings.openai_base_url
    if settings.anthropic_api_key and not os.environ.get("ANTHROPIC_API_KEY"):
        os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key


_setup_env()


async def _get_model_name() -> str:
    """Busca modelo do DB (prioridade) ou cai no .env."""
    from routers.settings import get_ai_config
    try:
        cfg = await get_ai_config()
        provider = cfg["provider"]
        model = cfg["model"]
    except Exception:
        provider = settings.ai_provider.lower()
        model = settings.anthropic_model if provider == "anthropic" else settings.openai_model

    if provider == "anthropic" and settings.anthropic_api_key:
        return f"anthropic:{model}"
    if settings.openai_api_key:
        # Remove base_url residual do DeepSeek se estiver configurado
        import os
        os.environ.pop("OPENAI_BASE_URL", None)
        return f"openai:{model}"
    raise ValueError("Nenhuma API key configurada")


_AGENT_INSTRUCTIONS = """## Papel
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


def _get_or_build_agent(model_name: str) -> Agent:
    if model_name in _agent_cache:
        return _agent_cache[model_name]
    agent = Agent(
        model=model_name,
        deps_type=QuoteDeps,
        output_type=QuoteOutput,
        instructions=_AGENT_INSTRUCTIONS,
    )
    agent.system_prompt(build_context)
    agent.output_validator(validate_quote)
    _agent_cache[model_name] = agent
    return agent


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


def _build_confirmed_products(
    answers: list[dict], catalog_map: dict, catalog: list[dict]
) -> list[dict]:
    """Camada 3c: devolve lista de {name_original, price, answer_value} para cada produto
    que o sistema classificou como CONFIRMADO (admin-mapped ou exact-match no CSV).

    Usado pelo validador para garantir que itens confirmados apareçam no devis mesmo
    que a IA os tenha omitido ou marcado erroneamente como 'A consulter'.
    """
    confirmed = []
    for answer in answers:
        value = str(answer.get("value", "")).strip()

        # Prioridade 1: admin mapeou via catalogProduct
        admin_product = catalog_map.get(value.lower(), "")
        if admin_product:
            match = _find_catalog_match(admin_product, catalog)
            if match:
                confirmed.append({"name": match["name_original"], "price": match["price"], "value": value})
            continue

        # Prioridade 2: match exato do value com CSV
        exact = next(
            (p for p in catalog if p["name"] == value.lower() or p["name_original"] == value),
            None,
        )
        if exact:
            confirmed.append({"name": exact["name_original"], "price": exact["price"], "value": value})

    return confirmed


async def validate_quote(ctx: RunContext[QuoteDeps], output: QuoteOutput) -> QuoteOutput:
    """Valide que les items existent dans le CSV et que les calculs sont corrects.

    Aplica as três sub-etapas da Camada 3 (ver docstring do módulo):
      3a: força preço do CSV para itens encontrados
      3b: força quantity=1 para itens adicionados pela IA (não solicitados)
      3c: re-injeta itens confirmados omitidos ou marcados errado pelo modelo
    """
    catalog = _parse_csv_catalog(ctx.deps.pricing_csv)
    client_mentions = _build_client_mentions(ctx.deps.answers, ctx.deps.catalog_map)

    if catalog:
        validated_items = []
        for item in output.items:
            match = _find_catalog_match(item.description, catalog)
            if match:
                # 3a: força preço do CSV
                item.unit_price = match["price"]
                # 3b: se a IA adicionou por conta própria, limita qty=1
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
                # Sem match → preço 0 + sufixo
                item.unit_price = 0
                item.quantity = 1
                item.subtotal = 0
                if "prix" not in item.description.lower() or "consulter" not in item.description.lower():
                    item.description = f"{item.description} (prix a consulter)"
                validated_items.append(item)

        # 3c: re-injeta confirmados que a IA omitiu ou marcou errado
        confirmed_products = _build_confirmed_products(
            ctx.deps.answers, ctx.deps.catalog_map, catalog
        )
        present_names = {it.description.lower().split(" (prix")[0] for it in validated_items}
        for cp in confirmed_products:
            name_lower = cp["name"].lower()
            # Verifica se já está presente com preço correto
            already_priced = any(
                name_lower in it.description.lower() and it.unit_price > 0
                for it in validated_items
            )
            if not already_priced:
                # Descobre a quantidade: procura na resposta original
                qty = 1
                for answer in ctx.deps.answers:
                    if str(answer.get("value", "")).strip() == cp["value"]:
                        try:
                            qty = int(answer.get("quantity", 1))
                        except (ValueError, TypeError):
                            qty = 1
                        break
                injected = QuoteItem(
                    description=cp["name"],
                    unit_price=cp["price"],
                    quantity=qty,
                    subtotal=round(cp["price"] * qty, 2),
                )
                validated_items.append(injected)
                logger.info(f"Camada 3c: item confirmado re-injetado: {cp['name']} @ ${cp['price']}")

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
            model_name = await _get_model_name()
            agent = _get_or_build_agent(model_name)
            result = await agent.run(
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
