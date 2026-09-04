"""Validador deterministico de fluxos — codigo puro, SEM IA, SEM I/O.

Implementa os invariantes de docs/referencia-fluxo.md. Toda geracao por IA
passa por aqui antes de virar draft. Retorna (erros, avisos):
- erros: fluxo invalido, nao pode ser salvo
- avisos: fluxo valido, mas exige acao humana no editor (ex.: imagens, CSV)
"""

RAMIFICADAS = {"single_choice", "yes_no"}


def validar_fluxo(flow: dict) -> tuple[list[str], list[str]]:
    erros: list[str] = []
    avisos: list[str] = []
    nodes = flow.get("nodes") or []
    edges = flow.get("edges") or []

    ids = [n.get("id") for n in nodes]
    if len(ids) != len(set(ids)):
        erros.append("IDs de nodes duplicados")
    por_id = {n.get("id"): n for n in nodes}

    starts = [n for n in nodes if n.get("type") == "start"]
    ends = [n for n in nodes if n.get("type") == "end"]
    if len(starts) != 1:
        erros.append(f"Deve existir exatamente 1 node 'start' (encontrados: {len(starts)})")
    if not ends:
        erros.append("Deve existir pelo menos 1 node 'end'")

    tipos_validos = {"start", "question", "message", "end"}
    for n in nodes:
        if n.get("type") not in tipos_validos:
            erros.append(f"Node '{n.get('id')}' tem tipo invalido: {n.get('type')}")

    # Edges referenciam nodes existentes; nada sai de end; nada entra em start
    saidas: dict[str, list[dict]] = {}
    for e in edges:
        s, t = e.get("source"), e.get("target")
        if s not in por_id or t not in por_id:
            erros.append(f"Edge '{e.get('id')}' referencia node inexistente ({s} -> {t})")
            continue
        if por_id[s].get("type") == "end":
            erros.append(f"Node 'end' '{s}' nao pode ter saida (end e terminal)")
        if por_id[t].get("type") == "start":
            erros.append(f"Nenhuma edge pode apontar para o 'start' ('{t}')")
        saidas.setdefault(s, []).append(e)

    # Handles duplicados por origem
    for s, lst in saidas.items():
        handles = [e.get("sourceHandle") for e in lst if e.get("sourceHandle")]
        if len(handles) != len(set(handles)):
            erros.append(f"Node '{s}' tem edges com sourceHandle duplicado")

    # Regras de saida por tipo
    for n in nodes:
        nid, tipo = n.get("id"), n.get("type")
        lst = saidas.get(nid, [])
        data = n.get("data") or {}
        if tipo == "end":
            continue
        if tipo == "question" and data.get("questionType") in RAMIFICADAS:
            opcoes = data.get("options") or []
            op_ids = {o.get("id") for o in opcoes}
            handles = {e.get("sourceHandle") for e in lst}
            if None in handles or "" in handles:
                erros.append(f"Pergunta ramificada '{nid}' tem edge sem sourceHandle")
            faltando = op_ids - handles
            sobrando = {h for h in handles if h} - op_ids
            if faltando:
                erros.append(f"Pergunta '{nid}': opcoes sem edge de saida: {sorted(faltando)}")
            if sobrando:
                erros.append(f"Pergunta '{nid}': edges com handle que nao e opcao: {sorted(sobrando)}")
            if len(opcoes) < 2:
                erros.append(f"Pergunta ramificada '{nid}' precisa de pelo menos 2 opcoes")
        else:
            if len(lst) != 1:
                erros.append(f"Node '{nid}' ({tipo}) deve ter exatamente 1 saida (tem {len(lst)})")
            elif lst[0].get("sourceHandle"):
                erros.append(f"Node '{nid}' ({tipo}) nao deve usar sourceHandle")

    if erros:
        return erros, avisos  # grafo quebrado: alcance/ciclo dariam falso-positivo

    # Alcancabilidade a partir do start (BFS)
    inicio = starts[0].get("id")
    visitados = set()
    fila = [inicio]
    while fila:
        atual = fila.pop()
        if atual in visitados:
            continue
        visitados.add(atual)
        for e in saidas.get(atual, []):
            fila.append(e.get("target"))
    orfaos = set(por_id) - visitados
    if orfaos:
        erros.append(f"Nodes inalcancaveis a partir do start: {sorted(orfaos)}")

    # Todo node alcanca um end (BFS reverso)
    entradas: dict[str, list[str]] = {}
    for e in edges:
        entradas.setdefault(e.get("target"), []).append(e.get("source"))
    alcanca_end = set()
    fila = [n.get("id") for n in ends]
    while fila:
        atual = fila.pop()
        if atual in alcanca_end:
            continue
        alcanca_end.add(atual)
        fila.extend(entradas.get(atual, []))
    becos = visitados - alcanca_end
    if becos:
        erros.append(f"Nodes sem caminho ate um 'end' (beco sem saida): {sorted(becos)}")

    # Ciclos (DFS com pilha)
    BRANCO, CINZA, PRETO = 0, 1, 2
    cor = {nid: BRANCO for nid in por_id}

    def tem_ciclo(nid: str) -> bool:
        cor[nid] = CINZA
        for e in saidas.get(nid, []):
            t = e.get("target")
            if cor[t] == CINZA:
                return True
            if cor[t] == BRANCO and tem_ciclo(t):
                return True
        cor[nid] = PRETO
        return False

    if any(cor[nid] == BRANCO and tem_ciclo(nid) for nid in por_id):
        erros.append("O fluxo contem ciclo (voltar a uma etapa ja visitada nao e permitido na v1)")

    # Orcamento: quote exige CSV; catalogProduct deve existir no CSV
    quote_ends = [n for n in ends if (n.get("data") or {}).get("endType") == "quote"]
    csv = (flow.get("pricing_csv") or "").strip()
    if quote_ends and not csv:
        avisos.append("Fluxo de orcamento sem tabela de precos: adicione o pricing_csv no editor antes de publicar")
    if csv:
        primeira_col = {l.split(",")[0].strip().lower() for l in csv.splitlines()[1:] if l.strip()}
        for n in nodes:
            data = n.get("data") or {}
            for o in data.get("options") or []:
                cp = (o.get("catalogProduct") or "").strip()
                if cp and cp.lower() not in primeira_col:
                    erros.append(f"Opcao '{o.get('label')}' referencia produto inexistente no CSV: '{cp}'")

    return erros, avisos
