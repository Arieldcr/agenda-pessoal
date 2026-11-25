from datetime import date

import pytest
from sqlmodel import Session, create_engine, select

from backend import database, db_recorrencia
from backend.db_recorrencia import Ocorrencia

ACADEMIA = {
    "titulo": "Academia",
    "frequencia": "semanal",
    "dias_semana": [5, 1, 3, 3],
    "inicio": "2026-11-02",
    "hora": "07:00",
    "duracao_min": 60,
    "categoria": "Saúde",
    "prioridade": "alta",
}


def criar(client, **extra):
    return client.post("/recorrencias", json={**ACADEMIA, **extra})


def test_cadastrar_semanal_devolve_201_e_dias_ordenados_sem_repeticao(client):
    resposta = criar(client)

    corpo = resposta.json()
    assert resposta.status_code == 201
    assert corpo["id"] == 1
    assert corpo["dias_semana"] == [1, 3, 5]
    assert corpo["hora"] == "07:00:00"
    assert corpo["inicio"] == "2026-11-02"
    assert corpo["fim"] is None


def test_cadastrar_diaria_e_mensal(client):
    diaria = client.post(
        "/recorrencias", json={"titulo": "Estudar", "frequencia": "diaria", "inicio": "2026-11-01"}
    )
    mensal = client.post(
        "/recorrencias",
        json={"titulo": "Revisar finanças", "frequencia": "mensal", "dia_do_mes": 5,
              "inicio": "2026-11-01", "fim": "2027-12-31"},
    )

    assert diaria.status_code == 201 and diaria.json()["intervalo"] == 1
    assert mensal.status_code == 201 and mensal.json()["dia_do_mes"] == 5


def test_semanal_sem_dias_e_aceita(client):
    resposta = criar(client, dias_semana=None)

    assert resposta.status_code == 201
    assert resposta.json()["dias_semana"] == []


def test_campos_que_nao_valem_para_a_frequencia_sao_descartados(client):
    resposta = client.post(
        "/recorrencias",
        json={"titulo": "Estudar", "frequencia": "diaria", "inicio": "2026-11-01",
              "dias_semana": [1, 3], "dia_do_mes": 5},
    )

    assert resposta.status_code == 201
    assert resposta.json()["dias_semana"] == []
    assert resposta.json()["dia_do_mes"] is None


@pytest.mark.parametrize(
    "extra",
    [
        {"frequencia": "anual"},
        {"intervalo": 0},
        {"intervalo": 366},
        {"dias_semana": [7]},
        {"frequencia": "mensal", "dias_semana": None, "dia_do_mes": 40},
        {"fim": "2026-10-01"},
        {"titulo": ""},
        {"titulo": "x" * 101},
        {"hora": None},
        {"prioridade": "urgente"},
        {"inicio": "amanhã"},
        {"campo_inexistente": 1},
    ],
    ids=[
        "frequencia", "intervalo-zero", "intervalo-alto", "dia-da-semana",
        "dia-do-mes", "fim-antes-do-inicio", "titulo-vazio", "titulo-longo",
        "duracao-sem-hora", "prioridade", "inicio-invalido", "campo-extra",
    ],
)
def test_cadastro_invalido_devolve_422_e_nao_grava(client, extra):
    resposta = criar(client, **extra)

    assert resposta.status_code == 422
    assert client.get("/recorrencias").json() == []


def test_cadastro_sem_inicio_ou_frequencia_devolve_422(client):
    assert client.post("/recorrencias", json={"titulo": "X", "frequencia": "diaria"}).status_code == 422
    assert client.post("/recorrencias", json={"titulo": "X", "inicio": "2026-11-01"}).status_code == 422


def test_listar_e_buscar(client):
    criar(client)
    criar(client, titulo="Outra")

    assert len(client.get("/recorrencias").json()) == 2
    assert client.get("/recorrencias/2").json()["titulo"] == "Outra"


def test_buscar_inexistente_devolve_404(client):
    assert client.get("/recorrencias/99").status_code == 404


def test_atualizar_so_o_titulo_preserva_o_resto(client):
    criar(client)

    resposta = client.patch("/recorrencias/1", json={"titulo": "Treino"})

    corpo = resposta.json()
    assert resposta.status_code == 200
    assert corpo["titulo"] == "Treino"
    assert corpo["dias_semana"] == [1, 3, 5]
    assert corpo["hora"] == "07:00:00"


def test_trocar_a_frequencia_descarta_os_dias_da_semana(client):
    criar(client)

    resposta = client.patch("/recorrencias/1", json={"frequencia": "diaria"})

    assert resposta.status_code == 200
    assert resposta.json()["dias_semana"] == []


def test_limpar_o_fim_e_a_categoria(client):
    criar(client, fim="2026-12-31")

    resposta = client.patch("/recorrencias/1", json={"fim": None, "categoria": None})

    assert resposta.json()["fim"] is None
    assert resposta.json()["categoria"] is None


@pytest.mark.parametrize(
    "corpo",
    [
        {"titulo": None},
        {"frequencia": None},
        {"inicio": None},
        {"dias_semana": [8]},
        {"fim": "2026-10-01"},
        {"hora": None},
        {"intervalo": 0},
        {"id": 5},
    ],
    ids=["titulo-null", "frequencia-null", "inicio-null", "dia-invalido",
         "fim-antes-do-inicio", "tirar-hora-com-duracao", "intervalo", "campo-id"],
)
def test_atualizacao_invalida_devolve_422_e_nao_altera(client, corpo):
    criar(client)
    antes = client.get("/recorrencias/1").json()

    resposta = client.patch("/recorrencias/1", json=corpo)

    assert resposta.status_code == 422
    assert client.get("/recorrencias/1").json() == antes


def test_atualizar_inexistente_devolve_404(client):
    assert client.patch("/recorrencias/99", json={"titulo": "X"}).status_code == 404


def test_excluir_recorrencia_apaga_tambem_o_estado_das_ocorrencias(client):
    criar(client)
    client.put("/recorrencias/1/ocorrencias/2026-11-04", json={"status": "concluida"})
    client.put("/recorrencias/1/ocorrencias/2026-11-06", json={"status": "cancelada"})

    resposta = client.delete("/recorrencias/1")

    assert resposta.status_code == 204
    assert client.get("/recorrencias/1").status_code == 404
    with Session(database.engine) as sessao:
        assert sessao.exec(select(Ocorrencia)).all() == []


def test_excluir_inexistente_devolve_404(client):
    assert client.delete("/recorrencias/99").status_code == 404


def test_migracao_cria_as_tabelas_novas_sem_perder_tarefas(tmp_path, monkeypatch):
    motor_antigo = create_engine(f"sqlite:///{(tmp_path / 'antigo.db').as_posix()}")
    with motor_antigo.begin() as conexao:
        conexao.exec_driver_sql(
            "CREATE TABLE tarefa (id INTEGER NOT NULL, titulo VARCHAR(100) NOT NULL, "
            "descricao VARCHAR, concluida BOOLEAN NOT NULL, PRIMARY KEY (id))"
        )
        conexao.exec_driver_sql("INSERT INTO tarefa (titulo, concluida) VALUES ('Antiga', 0)")
    monkeypatch.setattr(database, "engine", motor_antigo)

    database.criar_tabelas()

    assert [t.titulo for t in database.listar_tarefas()] == ["Antiga"]
    regra = db_recorrencia.cadastrar_recorrencia(
        {"titulo": "Nova", "frequencia": "diaria", "inicio": date(2026, 11, 1)}
    )
    assert regra.id == 1