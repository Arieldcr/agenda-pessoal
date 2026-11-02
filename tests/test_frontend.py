def test_pagina_inicial_do_frontend_e_entregue_em_app(client):
    resposta = client.get("/app/")

    assert resposta.status_code == 200
    assert resposta.headers["content-type"].startswith("text/html")
    assert "G.take" in resposta.text


def test_app_sem_barra_redireciona_para_app_com_barra(client):
    resposta = client.get("/app", follow_redirects=False)

    assert resposta.status_code == 307
    assert resposta.headers["location"].endswith("/app/")


def test_arquivos_de_estilo_e_script_sao_entregues(client):
    css = client.get("/app/style.css")
    js = client.get("/app/app.js")

    assert css.status_code == 200
    assert css.headers["content-type"].startswith("text/css")
    assert js.status_code == 200
    assert "javascript" in js.headers["content-type"]


def test_arquivo_inexistente_no_frontend_devolve_404(client):
    assert client.get("/app/nao-existe.js").status_code == 404


def test_api_e_documentacao_continuam_funcionando(client):
    assert client.get("/tarefas").status_code == 200
    assert client.get("/docs").status_code == 200
    assert client.get("/").json() == {
        "mensagem": "Assistente de Agenda Pessoal funcionando"
    }