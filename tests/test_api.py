def test_rota_raiz(client):
    resposta = client.get("/")
    assert resposta.status_code == 200
    assert resposta.json() == {"mensagem": "Assistente de Agenda Pessoal funcionando"}


def test_lista_comeca_vazia(client):
    resposta = client.get("/tarefas")
    assert resposta.status_code == 200
    assert resposta.json() == []