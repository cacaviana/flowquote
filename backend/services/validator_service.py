"""Validador pos-IA (Camada 3) do sistema anti-alucinacao.

Responsabilidades:
  3a: forca preco do CSV para cada item encontrado no catalogo
  3b: limita quantity=1 para itens adicionados pela IA sem solicitacao do cliente
  3b+: extrai quantidade total da descricao para produtos por unidade (ex: pied, metro)
  3c: re-injeta itens confirmados que a IA omitiu ou marcou erroneamente como "A consulter"
  Re-calcula subtotais, TPS (5%) e TVQ (9,975%)
"""

import logging
import re

from pydantic_ai import RunContext

from models.quote_deps import QuoteDeps
from schemas.quote import QuoteItem, QuoteOutput
from services.catalog_service import find_catalog_match, parse_csv_catalog

logger = logging.getLogger(__name__)


def build_client_mentions(answers: list[dict], catalog_map: dict) -> set[str]:
    """Conjunto de palavras-chave das respostas do cliente.

    Inclui valores das respostas, produtos mapeados pelo admin e palavras
    significativas dos titulos das perguntas.
    Usado pelo validador para distinguir itens solicitados pelo cliente
    de itens adicionados por iniciativa da IA (esses ficam com quantity=1).
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

    Camada 3c: devolve lista de {name, price, value} para cada produto
    que o sistema classificou como CONFIRMADO.
    Usado pelo validador para re-injetar itens que a IA omitiu
    ou marcou erroneamente como "A consulter".
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


async def validate_quote(ctx: RunContext[QuoteDeps], output: QuoteOutput) -> QuoteOutput:
    """Valide que les items existent dans le CSV et que les calculs sont corrects.

    Aplica as tres sub-etapas da Camada 3:
      3a: forca preco do CSV para itens encontrados
      3b: forca quantity=1 para itens adicionados pela IA (nao solicitados)
      3b+: extrai quantidade da descricao para produtos por unidade
      3c: re-injeta itens confirmados omitidos ou marcados errado pelo modelo
    """
    catalog = parse_csv_catalog(ctx.deps.pricing_csv)
    client_mentions = build_client_mentions(ctx.deps.answers, ctx.deps.catalog_map)

    if catalog:
        validated_items = []
        for item in output.items:
            match = find_catalog_match(item.description, catalog)
            if match:
                # 3a: forca preco do CSV
                item.unit_price = match["price"]
                # 3b: se a IA adicionou por conta propria, limita qty=1
                desc_lower = item.description.lower()
                client_requested = any(
                    mention in desc_lower or desc_lower in mention
                    for mention in client_mentions
                    if mention
                )
                if not client_requested:
                    item.quantity = 1
                # 3b+: para produtos por unidade com qty=1, tenta extrair quantidade da descricao
                # ex: "Cablage (12 pieds + 15 pieds = 27 pieds total)" → qty=27
                elif item.quantity == 1 and match.get("unit", "unidade") != "unidade":
                    numbers = [int(n) for n in re.findall(r'\b(\d+)\b', item.description) if int(n) > 1]
                    if numbers:
                        item.quantity = max(numbers)
                        logger.info(f"Qty extraida da descricao: {item.description!r} → qty={item.quantity}")
                item.subtotal = round(match["price"] * item.quantity, 2)
                validated_items.append(item)
            else:
                logger.warning(f"Item hors catalogue: {item.description} @ ${item.unit_price}")
                item.unit_price = 0
                item.quantity = 1
                item.subtotal = 0
                if "prix" not in item.description.lower() or "consulter" not in item.description.lower():
                    item.description = f"{item.description} (prix a consulter)"
                validated_items.append(item)

        # 3c: re-injeta confirmados que a IA omitiu ou marcou errado
        confirmed_products = build_confirmed_products(
            ctx.deps.answers, ctx.deps.catalog_map, catalog
        )
        for cp in confirmed_products:
            name_lower = cp["name"].lower()
            already_priced = any(
                name_lower in it.description.lower() and it.unit_price > 0
                for it in validated_items
            )
            if not already_priced:
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

    # Recalcula subtotais
    for item in output.items:
        expected = round(item.unit_price * item.quantity, 2)
        if abs(item.subtotal - expected) > 0.01:
            item.subtotal = expected

    # Recalcula totais
    subtotal = round(sum(i.subtotal for i in output.items), 2)
    output.subtotal = subtotal
    output.taxes_tps = round(subtotal * 0.05, 2)
    output.taxes_tvq = round(subtotal * 0.09975, 2)
    output.total = round(subtotal + output.taxes_tps + output.taxes_tvq, 2)

    return output
