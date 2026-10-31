import pytest


@pytest.mark.parametrize(
    "titulo",
    ["", "   ", "x" * 101],
    ids=["vazio", "so-espacos", "101-caracteres"],
)
def test_cadastro_recusa_titulo_invalido(client, titulo):
    resposta = client.post("/tarefas", json={"titulo": titulo})

    assert resposta.status_code == 422
    assert resposta.json()["detail"][0]["loc"] == ["body", "titulo"]
    # Um cadastro recusado não pode deixar nada gravado.
    assert client.get("/tarefas").json() == []


def test_cadastro_aceita_titulo_com_exatamente_100_caracteres(client):
    resposta = client.post("/tarefas", json={"titulo": "x" * 100})

    assert resposta.status_code == 201


def test_cadastro_exige_o_titulo(client):
    resposta = client.post("/tarefas", json={"descricao": "Sem título"})

    assert resposta.status_code == 422
    erro = resposta.json()["detail"][0]
    assert erro["type"] == "missing"
    assert erro["loc"] == ["body", "titulo"]


def test_cadastro_recusa_descricao_que_nao_e_texto(client):
    resposta = client.post("/tarefas", json={"titulo": "A", "descricao": 123})

    assert resposta.status_code == 422
    assert resposta.json()["detail"][0]["loc"] == ["body", "descricao"]


def test_cadastro_sem_corpo_devolve_422(client):
    resposta = client.post("/tarefas")

    assert resposta.status_code == 422


@pytest.mark.parametrize(
    "corpo",
    [
        {"titulo": ""},
        {"titulo": "   "},
        {"titulo": "x" * 101},
        {"titulo": None},
        {"concluida": None},
        {"concluida": "talvez"},
        {"id": 5},
        {"prioridade": "alta"},
    ],
    ids=[
        "titulo-vazio",
        "titulo-so-espacos",
        "titulo-longo",
        "titulo-null",
        "concluida-null",
        "concluida-invalida",
        "campo-id",
        "campo-desconhecido",
    ],
)
def test_atualizacao_recusa_dados_invalidos_e_nao_altera_a_tarefa(client, corpo):
    criada = client.post(
        "/tarefas", json={"titulo": "Original", "descricao": "Texto"}
    ).json()

    resposta = client.patch(f"/tarefas/{criada['id']}", json=corpo)

    assert resposta.status_code == 422
    # A tarefa continua exatamente como era.
    assert client.get(f"/tarefas/{criada['id']}").json() == criada


def test_atualizacao_nao_deixa_alterar_o_id(client):
    criada = client.post("/tarefas", json={"titulo": "Fixa"}).json()

    resposta = client.patch(f"/tarefas/{criada['id']}", json={"id": 99})

    erro = resposta.json()["detail"][0]
    assert resposta.status_code == 422
    assert erro["type"] == "extra_forbidden"
    assert erro["loc"] == ["body", "id"]


def test_atualizacao_com_corpo_vazio_nao_altera_nada(client):
    criada = client.post(
        "/tarefas", json={"titulo": "Igual", "descricao": "Mesma"}
    ).json()

    resposta = client.patch(f"/tarefas/{criada['id']}", json={})

    assert resposta.status_code == 200
    assert resposta.json() == criada
    