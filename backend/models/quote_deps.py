from dataclasses import dataclass


@dataclass
class QuoteDeps:
    """Dependencias injetadas no agente PydanticAI."""
    pricing_csv: str       # CSV bruto do tenant
    answers: list[dict]    # Respostas do formulario
    business_rules: str    # businessContext do EndNode
    ai_instruction: str    # aiInstruction do EndNode
    client_name: str
    client_email: str
    client_phone: str
    client_address: str
    catalog_map: dict      # { answer_value_lower → catalogProduct } — mapeamento do admin
