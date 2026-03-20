"""Parsing e matching de catalogo CSV.

Responsabilidades:
  - Converter CSV bruto em lista de produtos estruturados
  - Encontrar o produto do catalogo que melhor corresponde a uma descricao
  - Formatar o catalogo para inclusao no prompt da IA
"""

import csv
import io
import re


def parse_csv_catalog(csv_text: str) -> list[dict]:
    """Converte CSV bruto em lista de dicts com name, price, unit."""
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
                unit = row.get("unidade", "unidade").strip().lower() or "unidade"
                catalog.append({
                    "name": name.lower(),
                    "name_original": name,
                    "price": price,
                    "unit": unit,
                })
        return catalog
    except Exception:
        return []


def find_catalog_match(item_description: str, catalog: list[dict]) -> dict | None:
    """Encontra o produto do catalogo que melhor corresponde a descricao.

    Ordem de tentativas:
      1. Match exato (nome identico)
      2. Match parcial (um e subcadeia do outro)
      3. Match por palavras-chave com prefix matching para plurais (pied/pieds)

    Exige >= 2 palavras significativas para keyword match:
    evita que "camera" sozinha una produtos diferentes.
    """
    desc_lower = item_description.lower()

    # 1. Exact match
    for product in catalog:
        if product["name"] == desc_lower or product["name_original"].lower() == desc_lower:
            return product

    # 2. Partial match
    best_match = None
    best_len = 0
    for product in catalog:
        if product["name"] in desc_lower or desc_lower in product["name"]:
            if len(product["name"]) > best_len:
                best_match = product
                best_len = len(product["name"])

    if best_match:
        return best_match

    # 3. Keyword match com prefix matching para plurais franceses
    desc_words = {re.sub(r'[^\w]', '', w) for w in desc_lower.split()}
    desc_words.discard('')

    for product in catalog:
        prod_words = set(product["name"].split())
        meaningful = {
            w for w in prod_words
            if len(w) > 3 or (len(w) >= 2 and any(c.isdigit() for c in w))
        }
        if len(meaningful) < 2:
            continue
        # Todas as palavras significativas do produto devem aparecer na descricao.
        # Prefix match: "pied" casa com "pieds", "metro" com "metros".
        if all(
            any(dw == pw or (len(pw) >= 4 and dw.startswith(pw)) for dw in desc_words)
            for pw in meaningful
        ):
            if not best_match or len(meaningful) > best_len:
                best_match = product
                best_len = len(meaningful)

    return best_match


def format_csv_for_prompt(csv_text: str) -> str:
    """Formata catalogo CSV como tabela legivel para o prompt da IA."""
    catalog = parse_csv_catalog(csv_text)
    if not catalog:
        return "(Aucun catalogue charge)"
    lines = ["Produto | Preco | Unidade"]
    lines.append("-" * 40)
    for p in catalog:
        lines.append(f"{p['name_original']} | ${p['price']} | {p['unit']}")
    return "\n".join(lines)
