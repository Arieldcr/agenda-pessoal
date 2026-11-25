import pytest
from sqlmodel import Session, select

from backend import database
from backend.db_recorrencia import Ocorrencia

ACADEMIA = {
    "titulo": "Academia",
    "frequencia": "semanal",
    "dias_semana": [1, 3, 5],
    "inicio": "2026-11-02",
    "hora": "07:00",
    "duracao_min": 60,
}
QUARTA = "2026-11-04"  # uma ocorrência da regra (segunda, quarta e sexta)
TERCA = "2026-11-03"  # NÃO é uma ocorrência


@pytest.fixture
def academia(client):
    assert client.post("/recorrencias", json=ACADEMIA).status_code == 201


def url(dia=QUARTA, recorrencia_id=1):
    return f"/recorrencias/{recorrencia_id}/ocorrencias/{dia}"


def contar_estados():
    with Session(database.engine) as sessao:
        return len(sessao.exec(select(Ocorrencia)).all())


def test_concluir_uma_ocorrencia(client, academia):
    resposta = client.put(url(), json={"status": "concluida"})

    corpo = resposta.json()
    assert resposta.status_code == 200
    assert corpo["id"] == "r1-2026-11-04"
    assert corpo["tipo"] == "recorrente"
    assert corpo["status"] == "concluida"
    assert corpo["concluida"] is True
    assert corpo["titulo"] == "Academia"
    assert corpo["hora"] == "07:00:00"
    assert corpo["remarcada"] is False


def test_repetir_o_pedido_nao_duplica_o_registro(client, academia):
    client.put(url(), json={"status": "concluida"})
    client.put(url(), json={"status": "concluida"})
    client.put(url(), json={"status": "pendente"})

    assert contar_estados() == 1


def test_cada_ocorrencia_tem_estado_proprio(client, academia):
    client.put(url("2026-11-04"), json={"status": "concluida"})
    client.put(url("2026-11-06"), json={"status": "cancelada"})

    assert contar_estados() == 2
    assert client.put(url("2026-11-02"), json={}).json()["status"] == "pendente"


def test_data_que_nao_e_ocorrencia_devolve_404_e_nao_grava(client, academia):
    resposta = client.put(url(TERCA), json={"status": "concluida"})

    assert resposta.status_code == 404
    assert contar_estados() == 0


def test_antes_do_inicio_nao_e_ocorrencia(client, academia):
    assert client.put(url("2026-10-28"), json={"status": "concluida"}).status_code == 404


def test_recorrencia_inexistente_devolve_404(client):
    assert client.put(url(recorrencia_id=99), json={"status": "concluida"}).status_code == 404


def test_data_invalida_na_url_devolve_422(client, academia):
    assert client.put(url("2026-13-40"), json={"status": "concluida"}).status_code == 422


def test_remarcar_guarda_a_data_original(client, academia):
    resposta = client.put(url(), json={"dia": "2026-11-05"})

    corpo = resposta.json()
    assert resposta.status_code == 200
    assert corpo["data_original"] == "2026-11-04"
    assert corpo["dia"] == "2026-11-05"
    assert corpo["remarcada"] is True
    assert corpo["alterada"] is True


def test_alterar_so_esta_ocorrencia_e_voltar_ao_padrao_com_null(client, academia):
    mudou = client.put(url(), json={"titulo": "Treino de pernas", "hora": "18:30"}).json()
    assert mudou["titulo"] == "Treino de pernas"
    assert mudou["hora"] == "18:30:00"

    voltou = client.put(url(), json={"titulo": None, "hora": None}).json()

    assert voltou["titulo"] == "Academia"
    assert voltou["hora"] == "07:00:00"
    assert voltou["alterada"] is False
    assert client.get("/recorrencias/1").json()["titulo"] == "Academia"


@pytest.mark.parametrize(
    "corpo",
    [{"status": "feita"}, {"status": None}, {"titulo": ""}, {"prioridade": "urgente"},
     {"duracao_min": 0}, {"id": 3}],
    ids=["status-invalido", "status-null", "titulo-vazio", "prioridade", "duracao", "campo-extra"],
)
def test_dados_invalidos_devolvem_422_e_nao_gravam(client, academia, corpo):
    resposta = client.put(url(), json=corpo)

    assert resposta.status_code == 422
    assert contar_estados() == 0


def test_duracao_sem_hora_efetiva_devolve_422_e_nao_grava(client):
    client.post("/recorrencias", json={"titulo": "Sem hora", "frequencia": "diaria", "inicio": "2026-11-01"})

    resposta = client.put(url("2026-11-04"), json={"duracao_min": 30})

    assert resposta.status_code == 422
    assert contar_estados() == 0


def test_voltar_ao_padrao_apaga_o_estado_da_ocorrencia(client, academia):
    client.put(url(), json={"status": "concluida"})

    resposta = client.delete(url())

    assert resposta.status_code == 204
    assert contar_estados() == 0
    assert client.delete(url()).status_code == 404
    