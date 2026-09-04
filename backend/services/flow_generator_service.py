"""Gerador de fluxos por IA — one-shot deterministico.

Pipeline: descricao textual -> LLM (JSON) -> validador puro -> 1 tentativa de
reparo -> draft. A IA propoe; o validador (flow_validator.py) garante.
Cota: 10 geracoes/dia por tenant (colecao ai_generations).
Imagens: NUNCA geradas pela IA — imageUrl e removido e vira aviso.
"""
import json
import re
import unicodedata
from datetime import datetime, timezone

from config.settings import settings
from config.database import mongodb_client
from services.flow_validator import validar_fluxo

COTA_DIARIA = 10
RAMIFICADAS = {"single_choice", "yes_no"}


class QuotaExcedidaError(Exception):
    pass


_PROMPT_SISTEMA = """Tu geras fluxos de orcamento/captacao para o FlowQuote como JSON.
Responde SOMENTE com um objeto JSON valido, sem markdown, neste formato:

{"name": str, "nodes": [...], "edges": [...]}

REGRAS DO SCHEMA (obrigatorias):
- Node: {"id": str unico, "type": "start"|"question"|"message"|"end", "data": {...}}
- Exatamente 1 start (data: {"title": saudacao, "collectFields": ["name","email","phone"?]})
- question.data: {"title": pergunta, "questionType": "single_choice"|"yes_no"|"multiple_choice"|"dropdown"|"number"|"text"|"date"|"photo", "required": bool}
  - single_choice/yes_no/multiple_choice/dropdown: "options": [{"id": str, "label": str, "value": str}] (>=2)
  - number que representa quantidade de um produto: "quantityProduct": nome do produto
- message.data: {"title": str, "message": str}
- end.data: {"title": str, "endType": "quote"|"specialist"|"thank_you"|"scheduling"}
  - endType "quote" = gera ORCAMENTO (use quando o ramo leva a precos); adicione "businessContext" (regras do negocio) e "aiInstruction"
  - ramos sem valor terminam em "thank_you", "specialist" ou "scheduling"
- Edge: {"id": str, "source": nodeId, "target": nodeId, "sourceHandle"?: optionId, "label"?: str}

REGRAS DE LIGACAO (invariantes — o fluxo e REJEITADO se violar):
- single_choice/yes_no: exatamente 1 edge POR OPCAO, com sourceHandle = id da opcao
- start, message e demais questions: exatamente 1 edge de saida, SEM sourceHandle
- end: nenhuma saida; nada aponta para o start; sem ciclos; todo node alcanca um end
- NAO inclua position, imageUrl, tenant_id, status, pricing_csv (o sistema cuida)

CONTEUDO:
- Escreve titulos/perguntas/opcoes NA MESMA LINGUA da descricao do usuario
- 4 a 12 perguntas; ramifica quando a descricao indicar caminhos diferentes
- Se a descricao cita produtos com preco, o ramo principal termina em endType "quote"
"""


def _slugify(nome: str) -> str:
    s = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return (s or "fluxo") + "-" + datetime.now(timezone.utc).strftime("%m%d%H%M")


def _posicionar(flow: dict) -> None:
    """Layout automatico por niveis (BFS a partir do start)."""
    nodes = flow.get("nodes") or []
    edges = flow.get("edges") or []
    saidas: dict[str, list[str]] = {}
    for e in edges:
        saidas.setdefault(e.get("source"), []).append(e.get("target"))
    start = next((n["id"] for n in nodes if n.get("type") == "start"), None)
    nivel: dict[str, int] = {}
    fila = [(start, 0)] if start else []
    while fila:
        nid, lv = fila.pop(0)
        if nid in nivel:
            continue
        nivel[nid] = lv
        for t in saidas.get(nid, []):
            fila.append((t, lv + 1))
    contagem: dict[int, int] = {}
    for n in nodes:
        lv = nivel.get(n.get("id"), 0)
        col = contagem.get(lv, 0)
        contagem[lv] = col + 1
        n["position"] = {"x": 120 + col * 320, "y": 80 + lv * 180}


def _normalizar(flow: dict) -> list[str]:
    """Forca politicas do sistema; retorna avisos."""
    avisos: list[str] = []
    flow["status"] = "draft"
    flow.pop("tenant_id", None)
    flow.pop("pricing_csv", None)
    flow.pop("_id", None)
    if not flow.get("slug"):
        flow["slug"] = _slugify(flow.get("name") or "fluxo")
    com_imagem = 0
    for n in flow.get("nodes") or []:
        data = n.setdefault("data", {})
        if data.pop("imageUrl", None):
            com_imagem += 1
        # opcoes sem id ganham id deterministico
        for i, o in enumerate(data.get("options") or []):
            if not o.get("id"):
                o["id"] = f"{n.get('id')}-op{i+1}"
            if not o.get("value"):
                o["value"] = o.get("label", f"op{i+1}")
    if com_imagem:
        avisos.append(f"A IA nao escolhe imagens: {com_imagem} etapa(s) tiveram imagem removida")
    avisos.append("Adicione suas imagens nas etapas pelo editor (a IA nunca define imagens)")
    _posicionar(flow)
    return avisos


class FlowGeneratorService:
    async def _verificar_cota(self, tenant_id: str) -> None:
        db = mongodb_client.database
        inicio_dia = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        usados = await db["ai_generations"].count_documents(
            {"tenant_id": tenant_id, "at": {"$gte": inicio_dia}}
        )
        if usados >= COTA_DIARIA:
            raise QuotaExcedidaError(f"Cota diaria de {COTA_DIARIA} geracoes atingida")

    async def _chamar_llm(self, mensagens: list[dict]) -> tuple[dict, int, int]:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        resp = await client.chat.completions.create(
            model=settings.openai_model,
            messages=mensagens,
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=8000,
        )
        bruto = resp.choices[0].message.content or "{}"
        usage = resp.usage
        return json.loads(bruto), usage.prompt_tokens, usage.completion_tokens

    async def _registrar(self, tenant_id: str, ok: bool, t_in: int, t_out: int, erros: list[str]) -> None:
        try:
            await mongodb_client.database["ai_generations"].insert_one({
                "tenant_id": tenant_id,
                "at": datetime.now(timezone.utc),
                "model": settings.openai_model,
                "ok": ok,
                "tokens_input": t_in,
                "tokens_output": t_out,
                "erros": erros[:10],
            })
        except Exception:
            pass  # metering nunca derruba a geracao

    async def generate(self, description: str, tenant_id: str) -> dict:
        await self._verificar_cota(tenant_id)
        mensagens = [
            {"role": "system", "content": _PROMPT_SISTEMA},
            {"role": "user", "content": f"Descricao do fluxo desejado:\n\n{description}\n\nGera o JSON do fluxo."},
        ]
        flow, t_in, t_out = await self._chamar_llm(mensagens)
        avisos = _normalizar(flow)
        erros, avisos_val = validar_fluxo(flow)

        if erros:  # UMA unica tentativa de reparo — nunca loop
            mensagens.append({"role": "assistant", "content": json.dumps(flow, ensure_ascii=False)})
            mensagens.append({"role": "user", "content": (
                "O fluxo viola invariantes. Corrige TODOS os erros abaixo e devolve o JSON completo corrigido:\n- "
                + "\n- ".join(erros)
            )})
            flow, t_in2, t_out2 = await self._chamar_llm(mensagens)
            t_in, t_out = t_in + t_in2, t_out + t_out2
            avisos = _normalizar(flow)
            erros, avisos_val = validar_fluxo(flow)

        await self._registrar(tenant_id, not erros, t_in, t_out, erros)
        if erros:
            raise ValueError("A IA nao conseguiu gerar um fluxo valido: " + "; ".join(erros[:5]))
        return {"flow": flow, "avisos": avisos + avisos_val, "tokens_input": t_in, "tokens_output": t_out}
