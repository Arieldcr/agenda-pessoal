from sqlmodel import Session, select

from backend import database
from backend.db_recorrencia import Ocorrencia

ACADEMIA = {
    "titulo": "Academia",
    "frequencia": "semanal",
    "dias_semana": [1, 3, 5],  # segunda, quarta e sexta
    "inicio": "2026-11-02",
    "hora": "07:00",
    "duracao_min": 60,
}


def criar_regra(client, **extra):
    resposta = client.post("/recorrencias", json={**ACADEMIA, **extra})
    assert resposta.status_code == 201
    return resposta.json()["id"]


def agenda(client, de, ate):
    resposta = client.get("/agenda", params={"de": de, "ate": ate})
    assert resposta.status_code == 200
    return resposta.json()


def contar_estados():
    with Session(database.engine) as sessao:
        return len(sessao.exec(select(Ocorrencia)).all())


def url(dia, recorrencia_id=1):
    return f"/recorrencias/{recorrencia_id}/a-partir-de/{dia}"


# ===== Alterar esta e as próximas =====
def test_alterar_a_partir_de_divide_a_regra_em_duas(client):
    criar_regra(client)

    resposta = client.patch(url("2026-11-11"), json={"titulo": "Treino novo", "hora": "18:00"})

    nova = resposta.json()
    assert resposta.status_code == 200
    assert nova["id"] == 2
    assert nova["titulo"] == "Treino novo"
    assert nova["hora"] == "18:00:00"
    assert nova["inicio"] == "2026-11-11"
    assert nova["dias_semana"] == [1, 3, 5]
    antiga = client.get("/recorrencias/1").json()
    assert antiga["fim"] == "2026-11-10"
    assert antiga["titulo"] == "Academia"


def test_agenda_depois_da_divisao_nao_duplica_nem_perde_datas(client):
    criar_regra(client)
    client.patch(url("2026-11-11"), json={"titulo": "Treino novo"})

    itens = agenda(client, "2026-11-01", "2026-11-20")

    assert [(i["id"], i["titulo"]) for i in itens] == [
        ("r1-2026-11-02", "Academia"), ("r1-2026-11-04", "Academia"),
        ("r1-2026-11-06", "Academia"), ("r1-2026-11-09", "Academia"),
        ("r2-2026-11-11", "Treino novo"), ("r2-2026-11-13", "Treino novo"),
        ("r2-2026-11-16", "Treino novo"), ("r2-2026-11-18", "Treino novo"),
        ("r2-2026-11-20", "Treino novo"),
    ]


def test_estado_das_datas_seguintes_que_continuam_passa_para_a_regra_nova(client):
    criar_regra(client)
    client.put("/recorrencias/1/ocorrencias/2026-11-04", json={"status": "concluida"})
    client.put("/recorrencias/1/ocorrencias/2026-11-13", json={"status": "concluida"})

    client.patch(url("2026-11-11"), json={"hora": "18:00"})

    itens = {i["id"]: i for i in agenda(client, "2026-11-01", "2026-11-20")}
    assert itens["r1-2026-11-04"]["concluida"] is True
    assert itens["r2-2026-11-13"]["concluida"] is True
    assert "r1-2026-11-13" not in itens
    assert contar_estados() == 2


def test_estado_de_data_que_deixa_de_existir_e_descartado(client):
    criar_regra(client)
    client.put("/recorrencias/1/ocorrencias/2026-11-13", json={"status": "concluida"})

    client.patch(url("2026-11-11"), json={"dias_semana": [1]})  # só segundas

    assert contar_estados() == 0
    dias = [i["dia"] for i in agenda(client, "2026-11-11", "2026-11-20")]
    assert dias == ["2026-11-16"]


def test_a_partir_da_primeira_ocorrencia_e_o_mesmo_que_alterar_todas(client):
    criar_regra(client)

    resposta = client.patch(url("2026-11-02"), json={"titulo": "Todas"})

    assert resposta.status_code == 200
    assert resposta.json()["id"] == 1
    assert resposta.json()["inicio"] == "2026-11-02"
    assert len(client.get("/recorrencias").json()) == 1
    assert client.get("/recorrencias/1").json()["titulo"] == "Todas"


def test_a_nova_regra_herda_o_termino_da_antiga(client):
    criar_regra(client, fim="2026-12-31")

    nova = client.patch(url("2026-11-11"), json={"titulo": "Novo"}).json()

    assert nova["fim"] == "2026-12-31"
    assert client.get("/recorrencias/1").json()["fim"] == "2026-11-10"


def test_a_nova_serie_pode_comecar_depois_e_deixa_um_intervalo(client):
    criar_regra(client)

    nova = client.patch(url("2026-11-11"), json={"inicio": "2026-11-16"}).json()

    assert nova["inicio"] == "2026-11-16"
    dias = [i["dia"] for i in agenda(client, "2026-11-09", "2026-11-18")]
    assert dias == ["2026-11-09", "2026-11-16", "2026-11-18"]


def test_trocar_de_frequencia_na_divisao(client):
    criar_regra(client)

    nova = client.patch(url("2026-11-11"), json={"frequencia": "diaria"}).json()

    assert nova["frequencia"] == "diaria"
    assert nova["dias_semana"] == []
    assert len(agenda(client, "2026-11-11", "2026-11-17")) == 7


def test_regra_antiga_muito_longa_tambem_divide(client):
    criar_regra(client, frequencia="diaria", dias_semana=None, inicio="2024-01-01")

    resposta = client.patch(url("2026-11-11"), json={"titulo": "Novo"})

    assert resposta.status_code == 200
    assert client.get("/recorrencias/1").json()["fim"] == "2026-11-10"


def test_ocorrencia_anterior_muito_distante_conta_como_anterior(client):
    criar_regra(client, frequencia="mensal", dias_semana=None, dia_do_mes=10,
                inicio="2020-01-10", intervalo=24, hora=None, duracao_min=None)

    dividida = client.patch(url("2026-01-10"), json={"titulo": "Novo"})
    primeira = client.patch(url("2020-01-10"), json={"titulo": "Primeira"})

    assert dividida.json()["id"] == 2
    assert client.get("/recorrencias/1").json()["fim"] == "2026-01-09"
    assert primeira.json()["id"] == 1  # nada vem antes da primeira ocorrência


def test_data_que_nao_e_ocorrencia_ou_regra_inexistente_devolve_404(client):
    criar_regra(client)

    assert client.patch(url("2026-11-10"), json={"titulo": "X"}).status_code == 404  # terça
    assert client.patch(url("2026-11-11", recorrencia_id=99), json={"titulo": "X"}).status_code == 404
    assert client.patch(url("2026-13-40"), json={"titulo": "X"}).status_code == 422


def test_dados_invalidos_devolvem_422_e_nao_mudam_nada(client):
    criar_regra(client)
    client.put("/recorrencias/1/ocorrencias/2026-11-13", json={"status": "concluida"})

    for corpo in ({"intervalo": 0}, {"inicio": "2026-11-09"}, {"id": 5}, {"fim": "2026-11-01"}):
        assert client.patch(url("2026-11-11"), json=corpo).status_code == 422

    assert len(client.get("/recorrencias").json()) == 1
    assert client.get("/recorrencias/1").json()["fim"] is None
    assert contar_estados() == 1


# ===== Excluir esta e as próximas =====
def test_excluir_a_partir_de_termina_a_regra_na_vespera(client):
    criar_regra(client)
    client.put("/recorrencias/1/ocorrencias/2026-11-04", json={"status": "concluida"})
    client.put("/recorrencias/1/ocorrencias/2026-11-13", json={"status": "concluida"})

    resposta = client.delete(url("2026-11-11"))

    assert resposta.status_code == 204
    assert client.get("/recorrencias/1").json()["fim"] == "2026-11-10"
    dias = [i["dia"] for i in agenda(client, "2026-11-01", "2026-11-30")]
    assert dias == ["2026-11-02", "2026-11-04", "2026-11-06", "2026-11-09"]
    assert contar_estados() == 1  # o de 04/11 fica; o de 13/11 foi junto


def test_excluir_a_partir_da_primeira_ocorrencia_apaga_a_regra_inteira(client):
    criar_regra(client)
    client.put("/recorrencias/1/ocorrencias/2026-11-04", json={"status": "concluida"})

    resposta = client.delete(url("2026-11-02"))

    assert resposta.status_code == 204
    assert client.get("/recorrencias/1").status_code == 404
    assert contar_estados() == 0


def test_excluir_a_partir_de_data_que_nao_e_ocorrencia_ou_regra_inexistente(client):
    criar_regra(client)

    assert client.delete(url("2026-11-10")).status_code == 404
    assert client.delete(url("2026-11-11", recorrencia_id=99)).status_code == 404
    assert client.get("/recorrencias/1").json()["fim"] is None