def test_cadastrar_tarefa_devolve_201_e_a_tarefa(client):
    resposta = client.post(
        "/tarefas", json={"titulo": "Estudar", "descricao": "Capítulo 4"}
    )

    assert resposta.status_code == 201
    assert resposta.json() == {
        "id": 1,
        "titulo": "Estudar",
        "descricao": "Capítulo 4",
        "concluida": False,
    }


def test_tarefa_nasce_nao_concluida_e_descricao_e_opcional(client):
    resposta = client.post("/tarefas", json={"titulo": "Sem descrição"})

    assert resposta.status_code == 201
    assert resposta.json()["descricao"] is None
    assert resposta.json()["concluida"] is False


def test_titulo_tem_os_espacos_das_pontas_removidos(client):
    resposta = client.post("/tarefas", json={"titulo": "  Estudar  "})

    assert resposta.status_code == 201
    assert resposta.json()["titulo"] == "Estudar"


def test_listar_devolve_as_tarefas_cadastradas(client):
    client.post("/tarefas", json={"titulo": "Primeira"})
    client.post("/tarefas", json={"titulo": "Segunda"})

    resposta = client.get("/tarefas")

    assert resposta.status_code == 200
    titulos = [tarefa["titulo"] for tarefa in resposta.json()]
    # sorted: a API não promete uma ordem, então o teste também não depende dela.
    assert sorted(titulos) == ["Primeira", "Segunda"]


def test_buscar_tarefa_por_id(client):
    criada = client.post("/tarefas", json={"titulo": "Buscar"}).json()

    resposta = client.get(f"/tarefas/{criada['id']}")

    assert resposta.status_code == 200
    assert resposta.json() == criada