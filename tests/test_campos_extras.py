import pytest


def cadastrar(client, **extra):
    return client.post("/tarefas", json={"titulo": "Tarefa", **extra})


def test_cadastrar_com_todos_os_campos(client):
    resposta = cadastrar(
        client,
        dia="2026-11-20",
        hora="14:00",
        duracao_min=90,
        prioridade="alta",
        categoria="Estudos",
    )

    corpo = resposta.json()
    assert resposta.status_code == 201
    assert corpo["duracao_min"] == 90
    assert corpo["prioridade"] == "alta"
    assert corpo["categoria"] == "Estudos"


def test_campos_novos_sao_opcionais(client):
    corpo = cadastrar(client).json()

    assert corpo["duracao_min"] is None
    assert corpo["prioridade"] is None
    assert corpo["categoria"] is None


@pytest.mark.parametrize("prioridade", ["alta", "media", "baixa"])
def test_prioridades_validas(client, prioridade):
    assert cadastrar(client, prioridade=prioridade).status_code == 201


@pytest.mark.parametrize("prioridade", ["urgente", "ALTA", "", "1"])
def test_prioridade_invalida_devolve_422(client, prioridade):
    assert cadastrar(client, prioridade=prioridade).status_code == 422


@pytest.mark.parametrize("duracao", [1, 1440])
def test_duracao_nos_limites_e_aceita(client, duracao):
    resposta = cadastrar(client, dia="2026-11-20", hora="14:00", duracao_min=duracao)

    assert resposta.status_code == 201


@pytest.mark.parametrize("duracao", [0, -5, 1441, "muito"])
def test_duracao_invalida_devolve_422(client, duracao):
    resposta = cadastrar(client, dia="2026-11-20", hora="14:00", duracao_min=duracao)

    assert resposta.status_code == 422


def test_duracao_sem_hora_devolve_422_e_nao_grava(client):
    resposta = cadastrar(client, dia="2026-11-20", duracao_min=30)

    assert resposta.status_code == 422
    assert client.get("/tarefas").json() == []


def test_categoria_tem_espacos_removidos_e_vazia_vira_nula(client):
    assert cadastrar(client, categoria="  Estudos  ").json()["categoria"] == "Estudos"
    assert cadastrar(client, categoria="   ").json()["categoria"] is None


def test_categoria_aceita_30_caracteres_e_recusa_31(client):
    assert cadastrar(client, categoria="x" * 30).status_code == 201
    assert cadastrar(client, categoria="x" * 31).status_code == 422


def test_atualizar_e_limpar_prioridade_e_categoria(client):
    criada = cadastrar(client).json()
    url = f"/tarefas/{criada['id']}"

    resposta = client.patch(url, json={"prioridade": "media", "categoria": "Casa"})
    assert resposta.json()["prioridade"] == "media"
    assert resposta.json()["categoria"] == "Casa"

    resposta = client.patch(url, json={"prioridade": None, "categoria": None})
    assert resposta.json()["prioridade"] is None
    assert resposta.json()["categoria"] is None


def test_atualizar_duracao_sem_hora_devolve_422_e_nao_altera(client):
    criada = cadastrar(client, dia="2026-11-20").json()

    resposta = client.patch(f"/tarefas/{criada['id']}", json={"duracao_min": 30})

    assert resposta.status_code == 422
    assert client.get(f"/tarefas/{criada['id']}").json() == criada


def test_remover_a_hora_de_tarefa_com_duracao_devolve_422(client):
    criada = cadastrar(client, dia="2026-11-20", hora="14:00", duracao_min=30).json()

    resposta = client.patch(f"/tarefas/{criada['id']}", json={"hora": None})

    assert resposta.status_code == 422
    assert client.get(f"/tarefas/{criada['id']}").json() == criada


def test_remover_hora_e_duracao_juntas_funciona(client):
    criada = cadastrar(client, dia="2026-11-20", hora="14:00", duracao_min=30).json()

    resposta = client.patch(
        f"/tarefas/{criada['id']}", json={"hora": None, "duracao_min": None}
    )

    assert resposta.status_code == 200
    assert resposta.json()["hora"] is None
    assert resposta.json()["duracao_min"] is None