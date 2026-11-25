from datetime import date, time

import pytest
from sqlmodel import Session

from backend import database

ACADEMIA = {
    "titulo": "Academia",
    "frequencia": "semanal",
    "dias_semana": [1, 3, 5],  # segunda, quarta e sexta
    "inicio": "2026-11-02",
    "hora": "07:00",
    "duracao_min": 60,
}


def criar_tarefa(**campos):
    with Session(database.engine) as sessao:
        tarefa = database.Tarefa(**{"titulo": "Tarefa", **campos})
        sessao.add(tarefa)
        sessao.commit()
        sessao.refresh(tarefa)
        return tarefa.id


def criar_regra(client, **extra):
    resposta = client.post("/recorrencias", json={**ACADEMIA, **extra})
    assert resposta.status_code == 201
    return resposta.json()["id"]


def agenda(client, de, ate, **extra):
    resposta = client.get("/agenda", params={"de": de, "ate": ate, **extra})
    assert resposta.status_code == 200
    return resposta.json()


def ids(itens):
    return [item["id"] for item in itens]


def dias(itens):
    return [item["dia"] for item in itens]


def test_agenda_vazia(client):
    assert agenda(client, "2026-11-01", "2026-11-30") == []


def test_tarefa_avulsa_no_periodo_vem_no_formato_da_agenda(client):
    criar_tarefa(titulo="Estudar", dia=date(2026, 11, 10), hora=time(14, 0),
                 duracao_min=90, categoria="Estudos", prioridade="alta")

    [item] = agenda(client, "2026-11-01", "2026-11-30")

    assert item["id"] == "t1"
    assert item["tipo"] == "tarefa"
    assert item["tarefa_id"] == 1
    assert item["recorrencia_id"] is None
    assert item["data_original"] is None
    assert item["dia"] == "2026-11-10"
    assert item["hora"] == "14:00:00"
    assert item["duracao_min"] == 90
    assert item["status"] == "pendente"
    assert item["concluida"] is False


def test_tarefa_concluida_vem_como_concluida(client):
    criar_tarefa(dia=date(2026, 11, 10), concluida=True)

    [item] = agenda(client, "2026-11-01", "2026-11-30")

    assert item["status"] == "concluida"
    assert item["concluida"] is True


def test_limites_do_periodo_valem_inclusive(client):
    criar_tarefa(titulo="Primeiro", dia=date(2026, 11, 1))
    criar_tarefa(titulo="Ultimo", dia=date(2026, 11, 30))
    criar_tarefa(titulo="Antes", dia=date(2026, 10, 31))
    criar_tarefa(titulo="Depois", dia=date(2026, 12, 1))

    itens = agenda(client, "2026-11-01", "2026-11-30")

    assert [item["titulo"] for item in itens] == ["Primeiro", "Ultimo"]


def test_tarefa_sem_dia_so_entra_quando_pedido(client):
    criar_tarefa(titulo="Sem prazo")
    criar_tarefa(titulo="Com prazo", dia=date(2026, 11, 10))

    assert [i["titulo"] for i in agenda(client, "2026-11-01", "2026-11-30")] == ["Com prazo"]
    com_sem_dia = agenda(client, "2026-11-01", "2026-11-30", sem_dia="true")
    assert [i["titulo"] for i in com_sem_dia] == ["Com prazo", "Sem prazo"]


def test_regra_semanal_aparece_nas_datas_certas(client):
    criar_regra(client)

    itens = agenda(client, "2026-11-01", "2026-11-14")

    assert ids(itens) == [
        "r1-2026-11-02", "r1-2026-11-04", "r1-2026-11-06",
        "r1-2026-11-09", "r1-2026-11-11", "r1-2026-11-13",
    ]
    assert itens[0]["tipo"] == "recorrente"
    assert itens[0]["recorrencia_id"] == 1
    assert itens[0]["tarefa_id"] is None
    assert itens[0]["hora"] == "07:00:00"
    assert itens[0]["status"] == "pendente"


def test_cada_ocorrencia_tem_id_proprio(client):
    criar_regra(client, frequencia="diaria", dias_semana=None, inicio="2026-11-01")

    itens = agenda(client, "2026-11-01", "2026-12-12")

    assert len(itens) == 42
    assert len(set(ids(itens))) == 42


def test_ordem_por_dia_depois_hora_e_sem_hora_por_ultimo(client):
    criar_tarefa(titulo="Cedo", dia=date(2026, 11, 4), hora=time(6, 30))
    criar_tarefa(titulo="Sem hora", dia=date(2026, 11, 4))
    criar_regra(client)

    itens = agenda(client, "2026-11-04", "2026-11-04")

    assert ids(itens) == ["t1", "r1-2026-11-04", "t2"]


def test_ocorrencia_concluida_aparece_concluida_e_as_outras_continuam_pendentes(client):
    criar_regra(client)
    client.put("/recorrencias/1/ocorrencias/2026-11-04", json={"status": "concluida"})

    itens = agenda(client, "2026-11-01", "2026-11-07")

    assert {item["dia"]: item["concluida"] for item in itens} == {
        "2026-11-02": False, "2026-11-04": True, "2026-11-06": False,
    }


def test_ocorrencia_cancelada_some_da_agenda(client):
    criar_regra(client)
    client.put("/recorrencias/1/ocorrencias/2026-11-04", json={"status": "cancelada"})

    assert dias(agenda(client, "2026-11-01", "2026-11-07")) == ["2026-11-02", "2026-11-06"]


def test_ocorrencia_remarcada_dentro_do_periodo_muda_de_dia_sem_duplicar(client):
    criar_regra(client)
    client.put("/recorrencias/1/ocorrencias/2026-11-04", json={"dia": "2026-11-05"})

    itens = agenda(client, "2026-11-01", "2026-11-14")

    assert len(itens) == 6
    assert "2026-11-04" not in dias(itens)
    remarcada = next(item for item in itens if item["remarcada"])
    assert remarcada["dia"] == "2026-11-05"
    assert remarcada["data_original"] == "2026-11-04"
    assert remarcada["id"] == "r1-2026-11-04"


def test_ocorrencia_remarcada_para_fora_do_periodo_sai_dele(client):
    criar_regra(client)
    client.put("/recorrencias/1/ocorrencias/2026-11-30", json={"dia": "2026-12-01"})

    assert dias(agenda(client, "2026-11-24", "2026-11-30")) == ["2026-11-25", "2026-11-27"]


def test_ocorrencia_remarcada_vinda_de_fora_do_periodo_entra_nele(client):
    criar_regra(client)
    client.put("/recorrencias/1/ocorrencias/2026-11-30", json={"dia": "2026-12-01"})

    itens = agenda(client, "2026-12-01", "2026-12-07")

    assert dias(itens)[0] == "2026-12-01"
    assert itens[0]["data_original"] == "2026-11-30"
    assert itens[0]["remarcada"] is True


def test_alteracao_so_de_uma_ocorrencia_aparece_so_nela(client):
    criar_regra(client)
    client.put("/recorrencias/1/ocorrencias/2026-11-04",
               json={"titulo": "Treino de pernas", "hora": "18:30"})

    itens = {item["dia"]: item for item in agenda(client, "2026-11-02", "2026-11-06")}

    assert itens["2026-11-04"]["titulo"] == "Treino de pernas"
    assert itens["2026-11-04"]["hora"] == "18:30:00"
    assert itens["2026-11-04"]["alterada"] is True
    assert itens["2026-11-02"]["titulo"] == "Academia"
    assert itens["2026-11-02"]["alterada"] is False


def test_regra_respeita_inicio_e_fim(client):
    criar_regra(client, fim="2026-11-06")

    assert dias(agenda(client, "2026-11-01", "2026-11-14")) == [
        "2026-11-02", "2026-11-04", "2026-11-06",
    ]
    assert agenda(client, "2026-11-07", "2026-11-14") == []
    assert agenda(client, "2026-10-01", "2026-10-31") == []


def test_estado_de_data_que_a_regra_nao_gera_mais_e_ignorado(client):
    criar_regra(client)
    client.put("/recorrencias/1/ocorrencias/2026-11-04", json={"status": "concluida"})
    client.patch("/recorrencias/1", json={"dias_semana": [1]})  # agora só segundas

    itens = agenda(client, "2026-11-01", "2026-11-14")

    assert dias(itens) == ["2026-11-02", "2026-11-09"]


def test_regra_excluida_some_da_agenda(client):
    criar_regra(client)
    client.delete("/recorrencias/1")

    assert agenda(client, "2026-11-01", "2026-11-30") == []


def test_tarefas_e_recorrencias_juntas(client):
    criar_tarefa(titulo="Avulsa", dia=date(2026, 11, 9))
    criar_regra(client)

    itens = agenda(client, "2026-11-09", "2026-11-09")

    assert sorted(item["tipo"] for item in itens) == ["recorrente", "tarefa"]


@pytest.mark.parametrize(
    "params",
    [
        {"de": "2026-11-10", "ate": "2026-11-01"},
        {"de": "2026-01-01", "ate": "2027-12-31"},
        {"de": "2026-11-01"},
        {"ate": "2026-11-30"},
        {"de": "ontem", "ate": "2026-11-30"},
    ],
    ids=["periodo-invertido", "periodo-grande-demais", "sem-ate", "sem-de", "data-invalida"],
)
def test_periodo_invalido_devolve_422(client, params):
    assert client.get("/agenda", params=params).status_code == 422