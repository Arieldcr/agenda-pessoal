import pytest


def test_buscar_id_inexistente_devolve_404(client):
    resposta = client.get("/tarefas/999")

    assert resposta.status_code == 404
    assert resposta.json() == {"detail": "Tarefa não encontrada"}


def test_atualizar_id_inexistente_devolve_404(client):
    resposta = client.patch("/tarefas/999", json={"concluida": True})

    assert resposta.status_code == 404
    assert resposta.json() == {"detail": "Tarefa não encontrada"}


def test_excluir_id_inexistente_devolve_404(client):
    resposta = client.delete("/tarefas/999")

    assert resposta.status_code == 404
    assert resposta.json() == {"detail": "Tarefa não encontrada"}


def test_atualizar_id_inexistente_nao_cria_tarefa(client):
    client.patch("/tarefas/999", json={"titulo": "Fantasma"})

    assert client.get("/tarefas").json() == []


def test_excluir_a_mesma_tarefa_duas_vezes(client):
    criada = client.post("/tarefas", json={"titulo": "Apagar"}).json()

    primeira = client.delete(f"/tarefas/{criada['id']}")
    segunda = client.delete(f"/tarefas/{criada['id']}")

    assert primeira.status_code == 204
    assert segunda.status_code == 404


@pytest.mark.parametrize(
    "metodo, corpo",
    [
        ("get", None),
        ("patch", {"concluida": True}),
        ("delete", None),
    ],
)
def test_id_que_nao_e_numero_devolve_422(client, metodo, corpo):
    resposta = client.request(metodo, "/tarefas/abc", json=corpo)

    assert resposta.status_code == 422
    assert resposta.json()["detail"][0]["loc"] == ["path", "tarefa_id"]