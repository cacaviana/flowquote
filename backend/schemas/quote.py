from pydantic import BaseModel, Field


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
    recommendations: str = Field(description="Recommandations techniques basees sur les reponses")
    notes: str = Field(default="", description="Notes additionnelles (subventions, conditions)")
