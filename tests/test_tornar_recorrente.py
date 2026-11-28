from datetime import date

from sqlmodel import Session

from backend import database

REGRA = {
    "titulo": "Academia",
    "frequencia": "semanal",
    "dias_semana": [1, 3, 5],  # segunda, quarta e sexta
    "inicio": "2026-11-02",
    "hora": "07:00",
}


def criar_tarefa(**campos):
    with Session(database.engine) as sessao:
        tarefa = database.Tarefa(**{"titulo": "Tarefa", **campos})
        sessao.add(tarefa)
        sessao.commit()
        sessao.refresh(tarefa)
        return tarefa.id


def agenda(client, de, ate):
    resposta = client.get("/agenda", params={"de": de, "ate": ate})
    assert resposta.status_code == 200
    return resposta.json()


def test_tarefa_avulsa_vira_recorrente_e_deixa_de_existir_como_avulsa(client):
    tarefa_id = criar_tarefa(titulo="Academia", dia=date(2026, 11, 2))

    resposta = client.post(f"/tarefas/{tarefa_id}/recorrencia", json=REGRA)

    assert resposta.status_code == 201
    assert resposta.json()["id"] == 1
    assert resposta.json()["dias_semana"] == [1, 3, 5]
    assert database.listar_tarefas() == []
    assert len(client.get("/recorrencias").json()) == 1


def test_a_nova_regra_aparece_na_agenda_sem_duplicar_a_tarefa(client):
    tarefa_id = criar_tarefa(titulo="Academia", dia=date(2026, 11, 2))
    client.post(f"/tarefas/{tarefa_id}/recorrencia", json=REGRA)

    itens = agenda(client, "2026-11-01", "2026-11-07")

    assert [i["id"] for i in itens] == ["r1-2026-11-02", "r1-2026-11-04", "r1-2026-11-06"]
    assert all(i["tipo"] == "recorrente" for i in itens)


def test_tarefa_concluida_deixa_concluida_a_ocorrencia_da_mesma_data(client):
    tarefa_id = criar_tarefa(titulo="Academia", dia=date(2026, 11, 4), concluida=True)

    client.post(f"/tarefas/{tarefa_id}/recorrencia", json=REGRA)

    itens = {i["id"]: i for i in agenda(client, "2026-11-01", "2026-11-07")}
    assert itens["r1-2026-11-04"]["concluida"] is True
    assert itens["r1-2026-11-02"]["concluida"] is False
    assert itens["r1-2026-11-06"]["concluida"] is False


def test_tarefa_concluida_em_data_que_a_regra_nao_gera_nao_cria_estado(client):
    tarefa_id = criar_tarefa(titulo="Academia", dia=date(2026, 11, 3), concluida=True)  # terça

    resposta = client.post(f"/tarefas/{tarefa_id}/recorrencia", json=REGRA)

    assert resposta.status_code == 201
    assert all(not i["concluida"] for i in agenda(client, "2026-11-01", "2026-11-07"))


def test_tarefa_inexistente_devolve_404_e_nao_cria_regra(client):
    resposta = client.post("/tarefas/99/recorrencia", json=REGRA)

    assert resposta.status_code == 404
    assert client.get("/recorrencias").json() == []


def test_regra_invalida_devolve_422_e_a_tarefa_continua_como_estava(client):
    tarefa_id = criar_tarefa(titulo="Academia", dia=date(2026, 11, 2))

    for corpo in ({**REGRA, "intervalo": 0}, {**REGRA, "fim": "2026-10-01"},
                  {**REGRA, "hora": None, "duracao_min": 30}):
        assert client.post(f"/tarefas/{tarefa_id}/recorrencia", json=corpo).status_code == 422

    assert [t.titulo for t in database.listar_tarefas()] == ["Academia"]
    assert client.get("/recorrencias").json() == []