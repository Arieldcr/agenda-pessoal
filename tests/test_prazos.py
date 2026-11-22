from sqlmodel import create_engine

from backend import database


def cadastrar(client, **extra):
    return client.post("/tarefas", json={"titulo": "Com prazo", **extra})


def test_cadastrar_com_dia_e_hora(client):
    resposta = cadastrar(client, dia="2026-11-18", hora="14:00")

    assert resposta.status_code == 201
    assert resposta.json()["dia"] == "2026-11-18"
    assert resposta.json()["hora"] == "14:00:00"


def test_cadastrar_so_com_dia_deixa_a_hora_vazia(client):
    resposta = cadastrar(client, dia="2026-11-18")

    assert resposta.status_code == 201
    assert resposta.json()["hora"] is None


def test_tarefa_sem_prazo_continua_valida(client):
    resposta = cadastrar(client)

    assert resposta.status_code == 201
    assert resposta.json()["dia"] is None
    assert resposta.json()["hora"] is None


def test_hora_sem_dia_devolve_422_e_nao_grava(client):
    resposta = cadastrar(client, hora="14:00")

    assert resposta.status_code == 422
    assert client.get("/tarefas").json() == []


def test_dia_e_hora_invalidos_devolvem_422(client):
    assert cadastrar(client, dia="2026-13-40").status_code == 422
    assert cadastrar(client, dia="2026-11-18", hora="25:99").status_code == 422
    assert cadastrar(client, dia="amanhã").status_code == 422


def test_atualizar_dia_e_hora(client):
    criada = cadastrar(client).json()

    resposta = client.patch(f"/tarefas/{criada['id']}", json={"dia": "2026-11-20", "hora": "09:30"})

    assert resposta.status_code == 200
    assert resposta.json()["dia"] == "2026-11-20"
    assert resposta.json()["hora"] == "09:30:00"


def test_atualizar_so_a_hora_quando_a_tarefa_ja_tem_dia(client):
    criada = cadastrar(client, dia="2026-11-18").json()

    resposta = client.patch(f"/tarefas/{criada['id']}", json={"hora": "08:00"})

    assert resposta.status_code == 200
    assert resposta.json()["hora"] == "08:00:00"


def test_atualizar_hora_sem_dia_devolve_422_e_nao_altera(client):
    criada = cadastrar(client).json()

    resposta = client.patch(f"/tarefas/{criada['id']}", json={"hora": "08:00"})

    assert resposta.status_code == 422
    assert client.get(f"/tarefas/{criada['id']}").json() == criada


def test_remover_so_o_dia_de_tarefa_com_hora_devolve_422(client):
    criada = cadastrar(client, dia="2026-11-18", hora="14:00").json()

    resposta = client.patch(f"/tarefas/{criada['id']}", json={"dia": None})

    assert resposta.status_code == 422
    assert client.get(f"/tarefas/{criada['id']}").json() == criada


def test_remover_dia_e_hora_juntos_funciona(client):
    criada = cadastrar(client, dia="2026-11-18", hora="14:00").json()

    resposta = client.patch(f"/tarefas/{criada['id']}", json={"dia": None, "hora": None})

    assert resposta.status_code == 200
    assert resposta.json()["dia"] is None
    assert resposta.json()["hora"] is None


def test_migracao_acrescenta_colunas_sem_perder_dados(tmp_path, monkeypatch):
    motor_antigo = create_engine(f"sqlite:///{(tmp_path / 'antigo.db').as_posix()}")
    with motor_antigo.begin() as conexao:
        conexao.exec_driver_sql(
            "CREATE TABLE tarefa (id INTEGER NOT NULL, titulo VARCHAR(100) NOT NULL, "
            "descricao VARCHAR, concluida BOOLEAN NOT NULL, PRIMARY KEY (id))"
        )
        conexao.exec_driver_sql(
            "INSERT INTO tarefa (titulo, descricao, concluida) VALUES ('Antiga', 'texto', 1)"
        )
    monkeypatch.setattr(database, "engine", motor_antigo)

    database.criar_tabelas()
    database.criar_tabelas()  # rodar duas vezes não pode dar erro

    tarefas = database.listar_tarefas()
    assert len(tarefas) == 1
    assert tarefas[0].titulo == "Antiga"
    assert tarefas[0].concluida is True
    assert tarefas[0].dia is None and tarefas[0].hora is None
    assert tarefas[0].duracao_min is None
    assert tarefas[0].prioridade is None and tarefas[0].categoria is None