def test_atualizar_so_o_titulo_preserva_o_resto(client):
    criada = client.post(
        "/tarefas", json={"titulo": "Antigo", "descricao": "Original"}
    ).json()

    resposta = client.patch(f"/tarefas/{criada['id']}", json={"titulo": "Novo"})

    assert resposta.status_code == 200
    assert resposta.json() == {
        "id": criada["id"],
        "titulo": "Novo",
        "descricao": "Original",
        "concluida": False,
    }


def test_marcar_tarefa_como_concluida(client):
    criada = client.post("/tarefas", json={"titulo": "Terminar"}).json()
    assert criada["concluida"] is False

    resposta = client.patch(f"/tarefas/{criada['id']}", json={"concluida": True})

    assert resposta.status_code == 200
    assert resposta.json()["concluida"] is True


def test_desmarcar_a_conclusao(client):
    criada = client.post("/tarefas", json={"titulo": "Reabrir"}).json()
    client.patch(f"/tarefas/{criada['id']}", json={"concluida": True})

    resposta = client.patch(f"/tarefas/{criada['id']}", json={"concluida": False})

    assert resposta.status_code == 200
    assert resposta.json()["concluida"] is False


def test_apagar_a_descricao_enviando_null(client):
    criada = client.post(
        "/tarefas", json={"titulo": "Com descrição", "descricao": "Apagar"}
    ).json()

    resposta = client.patch(f"/tarefas/{criada['id']}", json={"descricao": None})

    assert resposta.status_code == 200
    assert resposta.json()["descricao"] is None
    assert resposta.json()["titulo"] == "Com descrição"


def test_atualizar_varios_campos_de_uma_vez(client):
    criada = client.post("/tarefas", json={"titulo": "A", "descricao": "B"}).json()

    resposta = client.patch(
        f"/tarefas/{criada['id']}",
        json={"titulo": "  C  ", "descricao": "D", "concluida": True},
    )

    assert resposta.status_code == 200
    assert resposta.json() == {
        "id": criada["id"],
        "titulo": "C",
        "descricao": "D",
        "concluida": True,
    }


def test_atualizacao_fica_gravada_no_banco(client):
    criada = client.post("/tarefas", json={"titulo": "Antes"}).json()
    client.patch(f"/tarefas/{criada['id']}", json={"titulo": "Depois"})

    resposta = client.get(f"/tarefas/{criada['id']}")

    assert resposta.status_code == 200
    assert resposta.json()["titulo"] == "Depois"