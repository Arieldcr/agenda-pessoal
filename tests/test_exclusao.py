def test_excluir_tarefa_devolve_204_sem_corpo(client):
    criada = client.post("/tarefas", json={"titulo": "Apagar"}).json()

    resposta = client.delete(f"/tarefas/{criada['id']}")

    assert resposta.status_code == 204
    assert resposta.content == b""


def test_tarefa_excluida_some_da_busca_e_da_listagem(client):
    criada = client.post("/tarefas", json={"titulo": "Apagar"}).json()
    client.delete(f"/tarefas/{criada['id']}")

    assert client.get(f"/tarefas/{criada['id']}").status_code == 404
    assert client.get("/tarefas").json() == []


def test_excluir_nao_afeta_as_outras_tarefas(client):
    manter = client.post("/tarefas", json={"titulo": "Manter"}).json()
    apagar = client.post("/tarefas", json={"titulo": "Apagar"}).json()

    client.delete(f"/tarefas/{apagar['id']}")

    restantes = client.get("/tarefas").json()
    assert restantes == [manter]


def test_ciclo_de_vida_completo_de_uma_tarefa(client):
    # cadastrar
    criada = client.post(
        "/tarefas", json={"titulo": "Ciclo", "descricao": "Do começo ao fim"}
    ).json()
    tarefa_id = criada["id"]

    # buscar
    assert client.get(f"/tarefas/{tarefa_id}").json() == criada

    # atualizar
    atualizada = client.patch(
        f"/tarefas/{tarefa_id}", json={"titulo": "Ciclo editado", "concluida": True}
    ).json()
    assert atualizada["titulo"] == "Ciclo editado"
    assert atualizada["concluida"] is True
    assert atualizada["descricao"] == "Do começo ao fim"

    # excluir
    assert client.delete(f"/tarefas/{tarefa_id}").status_code == 204
    assert client.get(f"/tarefas/{tarefa_id}").status_code == 404