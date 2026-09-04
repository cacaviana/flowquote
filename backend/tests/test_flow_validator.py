"""Testes do validador deterministico de fluxos — puro, sem rede/IA."""
from services.flow_validator import validar_fluxo


def _n(nid, tipo, **data):
    return {"id": nid, "type": tipo, "data": data}


def _e(eid, s, t, handle=None):
    e = {"id": eid, "source": s, "target": t}
    if handle:
        e["sourceHandle"] = handle
    return e


def _fluxo_valido():
    return {
        "nodes": [
            _n("s", "start", title="Ola"),
            _n("q1", "question", title="Tipo?", questionType="single_choice",
               options=[{"id": "o1", "label": "A", "value": "a"}, {"id": "o2", "label": "B", "value": "b"}]),
            _n("q2", "question", title="Qtd?", questionType="number"),
            _n("m", "message", title="Info", message="ok"),
            _n("e1", "end", title="Fim", endType="thank_you"),
            _n("e2", "end", title="Fim2", endType="specialist"),
        ],
        "edges": [
            _e("a", "s", "q1"),
            _e("b", "q1", "q2", "o1"),
            _e("c", "q1", "m", "o2"),
            _e("d", "q2", "e1"),
            _e("f", "m", "e2"),
        ],
    }


def test_fluxo_valido_passa():
    erros, _ = validar_fluxo(_fluxo_valido())
    assert erros == []


def test_dois_starts():
    f = _fluxo_valido(); f["nodes"].append(_n("s2", "start"))
    erros, _ = validar_fluxo(f)
    assert any("exatamente 1" in e for e in erros)


def test_sem_end():
    f = {"nodes": [_n("s", "start")], "edges": []}
    erros, _ = validar_fluxo(f)
    assert any("pelo menos 1 node 'end'" in e for e in erros)


def test_end_com_saida():
    f = _fluxo_valido(); f["edges"].append(_e("x", "e1", "m"))
    erros, _ = validar_fluxo(f)
    assert any("terminal" in e for e in erros)


def test_edge_para_start():
    f = _fluxo_valido(); f["edges"].append(_e("x", "m", "s"))
    erros, _ = validar_fluxo(f)
    assert any("apontar para o 'start'" in e for e in erros)


def test_opcao_sem_edge():
    f = _fluxo_valido(); f["edges"] = [e for e in f["edges"] if e["id"] != "c"]
    erros, _ = validar_fluxo(f)
    assert any("opcoes sem edge" in e for e in erros)


def test_handle_duplicado():
    f = _fluxo_valido(); f["edges"].append(_e("x", "q1", "e1", "o1"))
    erros, _ = validar_fluxo(f)
    assert any("duplicado" in e for e in erros)


def test_node_orfao():
    f = _fluxo_valido(); f["nodes"].append(_n("z", "message", message="perdido")); f["edges"].append(_e("zz", "z", "e1"))
    erros, _ = validar_fluxo(f)
    assert any("inalcancaveis" in e for e in erros)


def test_beco_sem_saida():
    f = _fluxo_valido()
    f["nodes"].append(_n("q3", "question", questionType="text"))
    f["edges"] = [e for e in f["edges"] if e["id"] != "d"] + [_e("d", "q2", "q3"), _e("g", "q3", "q2")]
    erros, _ = validar_fluxo(f)
    assert any("ciclo" in e.lower() or "beco" in e for e in erros)


def test_ciclo():
    f = _fluxo_valido(); f["edges"] = [e for e in f["edges"] if e["id"] != "d"] + [_e("d", "q2", "q1")]
    erros, _ = validar_fluxo(f)
    assert erros  # ramificada ganha edge extra sem handle OU ciclo — ambos invalidos


def test_quote_sem_csv_e_aviso_nao_erro():
    f = _fluxo_valido()
    f["nodes"] = [n if n["id"] != "e1" else _n("e1", "end", endType="quote") for n in f["nodes"]]
    erros, avisos = validar_fluxo(f)
    assert erros == []
    assert any("pricing_csv" in a for a in avisos)


def test_catalog_product_inexistente_no_csv():
    f = _fluxo_valido()
    f["pricing_csv"] = "produto,preco\nPainel Solar,1000"
    f["nodes"][1]["data"]["options"][0]["catalogProduct"] = "Produto Fantasma"
    erros, _ = validar_fluxo(f)
    assert any("inexistente no CSV" in e for e in erros)


def test_tipo_invalido():
    f = _fluxo_valido(); f["nodes"].append(_n("w", "widget"))
    erros, _ = validar_fluxo(f)
    assert any("tipo invalido" in e for e in erros)
