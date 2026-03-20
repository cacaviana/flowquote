"""Construcao do prompt de sistema para o agente de orcamento.

Responsabilidades:
  - Classificar respostas do cliente em CONFIRMADOS / AUSENTES / CONTEXTO
  - Montar o system prompt com as tres secoes
  - Construir o conjunto de palavras mencionadas pelo cliente (para o validador)
  - Identificar produtos confirmados (para re-injecao pelo validador)
"""

from pydantic_ai import RunContext
from models.quote_deps import QuoteDeps
from services.catalog_service import parse_csv_catalog, find_catalog_match, format_csv_for_prompt


def build_context(ctx: RunContext[QuoteDeps]) -> str:
    """Injeta o contexto completo no prompt de sistema.

    Classifica cada resposta em tres buckets:
      CONFIRMADOS — produto mapeado pelo admin ou match exato no CSV
      AUSENTES    — produto mapeado mas nao existe no CSV
      OUTROS      — contexto puro (regiao, amperagem, nome) ou sem match
    """
    catalog = parse_csv_catalog(ctx.deps.pricing_csv)
    csv_table = format_csv_for_prompt(ctx.deps.pricing_csv)

    confirmed: list[str] = []
    absent: list[str] = []
    context_answers: list[str] = []

    for answer in ctx.deps.answers:
        value = str(answer.get("value", "")).strip()
        question = answer.get("question", answer.get("node_id", "?"))

        # Prioridade 1: admin mapeou explicitamente via catalogProduct
        admin_product = ctx.deps.catalog_map.get(value.lower(), "")
        if admin_product:
            if catalog:
                match = find_catalog_match(admin_product, catalog)
                if match:
                    confirmed.append(
                        f"  - {admin_product} @ ${match['price']} (cliente escolheu \"{value}\")"
                    )
                else:
                    absent.append(
                        f"  - \"{value}\" → \"{admin_product}\" ausente do CSV → preco 0 + \"(prix a consulter)\""
                    )
            else:
                absent.append(
                    f"  - \"{value}\" → \"{admin_product}\" (sem CSV) → preco 0 + \"(prix a consulter)\""
                )
            continue

        # Prioridade 2: auto-deteccao por match exato
        if catalog:
            exact = next(
                (p for p in catalog if p["name"] == value.lower() or p["name_original"] == value),
                None,
            )
            if exact:
                confirmed.append(
                    f"  - {exact['name_original']} @ ${exact['price']} (auto-detectado de \"{value}\")"
                )
                continue

        context_answers.append(f"  - {question}: {value}")

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
            "(Contexto tecnico — regiao, amperagem, etc. — OU descricoes que NAO constam no catalogo.\n"
            "REGRA: Se relevante ao devis, incluir com DESCRICAO EXATA do cliente. "
            "Se nao estiver no catalogo: preco 0 + \"(prix a consulter)\". "
            "INTERDIT de inventar preco. Dados pessoais (nome, email, telefone) NUNCA sao itens.)\n"
            + "\n".join(context_answers)
        )

    prompt = (
        f"CATALOGUE DE PRIX (source de verite ABSOLUE):\n"
        f"{csv_table}"
        f"{confirmed_section}{absent_section}{other_section}\n\n"
        f"REGRAS:\n"
        f"1. PRODUTOS CONFIRMADOS acima DEVEM estar no devis com preco exato\n"
        f"2. Preco de qualquer item DEVE ser do catalogo — JAMAIS inventar\n"
        f"3. Para produtos por unidade, multiplicar preco x quantidade\n"
        f"4. Servico sem preco no catalogo: preco 0 + \"(prix a consulter)\"\n"
        f"5. Dados pessoais do cliente NUNCA sao itens do devis\n\n"
        f"CLIENT:\n"
        f"Nom: {ctx.deps.client_name}\n"
        f"Email: {ctx.deps.client_email}\n"
        f"Tel: {ctx.deps.client_phone or 'N/A'}\n"
        f"Adresse: {ctx.deps.client_address or 'N/A'}"
    )

    if ctx.deps.business_rules:
        prompt += f"\n\nREGLES METIER:\n{ctx.deps.business_rules}"

    if ctx.deps.ai_instruction:
        prompt += f"\n\nINSTRUCTIONS DE FORMAT:\n{ctx.deps.ai_instruction}"

    return prompt


def build_client_mentions(answers: list[dict], catalog_map: dict) -> set[str]:
    """Conjunto de palavras-chave das respostas do cliente.

    Usado pelo validador para distinguir itens solicitados pelo cliente
    de itens adicionados por iniciativa da IA.
    """
    mentioned: set[str] = set()
    for answer in answers:
        value = str(answer.get("value", "")).strip()
        question = str(answer.get("question", "")).strip()
        admin_product = catalog_map.get(value.lower(), "")
        if admin_product:
            mentioned.add(admin_product.lower())
        mentioned.add(value.lower())
        for word in question.lower().split():
            if len(word) > 4:
                mentioned.add(word)
    return mentioned


def build_confirmed_products(
    answers: list[dict], catalog_map: dict, catalog: list[dict]
) -> list[dict]:
    """Lista de produtos confirmados (admin-mapped ou exact-match no CSV).

    Usado pelo validador (Camada 3c) para re-injetar itens que a IA omitiu
    ou marcou erroneamente como 'A consulter'.
    """
    confirmed = []
    for answer in answers:
        value = str(answer.get("value", "")).strip()

        admin_product = catalog_map.get(value.lower(), "")
        if admin_product:
            match = find_catalog_match(admin_product, catalog)
            if match:
                confirmed.append({"name": match["name_original"], "price": match["price"], "value": value})
            continue

        exact = next(
            (p for p in catalog if p["name"] == value.lower() or p["name_original"] == value),
            None,
        )
        if exact:
            confirmed.append({"name": exact["name_original"], "price": exact["price"], "value": value})

    return confirmed
