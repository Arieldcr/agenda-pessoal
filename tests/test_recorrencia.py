from datetime import date

import pytest

from backend.recorrencia import Regra, dia_da_semana, ocorrencias


def d(texto):
    ano, mes, dia = map(int, texto.split("-"))
    return date(ano, mes, dia)


def datas(regra, de, ate):
    return [dia.isoformat() for dia in ocorrencias(regra, d(de), d(ate))]


def test_dia_da_semana_comeca_no_domingo():
    assert dia_da_semana(d("2026-11-01")) == 0  # domingo
    assert dia_da_semana(d("2026-11-02")) == 1  # segunda
    assert dia_da_semana(d("2026-11-07")) == 6  # sábado


# ===== Diária =====
def test_todos_os_dias():
    regra = Regra("diaria", d("2026-11-01"))

    assert len(datas(regra, "2026-11-01", "2026-11-07")) == 7


def test_a_cada_3_dias():
    regra = Regra("diaria", d("2026-11-01"), intervalo=3)

    assert datas(regra, "2026-11-01", "2026-11-15") == [
        "2026-11-01", "2026-11-04", "2026-11-07", "2026-11-10", "2026-11-13",
    ]


def test_periodo_que_comeca_depois_do_inicio_mantem_o_ritmo():
    regra = Regra("diaria", d("2026-11-01"), intervalo=3)

    assert datas(regra, "2026-11-05", "2026-11-15") == [
        "2026-11-07", "2026-11-10", "2026-11-13",
    ]


def test_data_de_termino_vale_inclusive():
    regra = Regra("diaria", d("2026-11-01"), intervalo=3, fim=d("2026-11-10"))

    assert datas(regra, "2026-11-01", "2026-11-30")[-1] == "2026-11-10"


def test_periodo_antes_do_inicio_ou_depois_do_fim_nao_tem_ocorrencias():
    regra = Regra("diaria", d("2026-11-10"), fim=d("2026-11-20"))

    assert datas(regra, "2026-11-01", "2026-11-09") == []
    assert datas(regra, "2026-11-21", "2026-11-30") == []


# ===== Semanal =====
def test_segunda_quarta_e_sexta():
    regra = Regra("semanal", d("2026-11-01"), dias_semana=(1, 3, 5))

    assert datas(regra, "2026-11-01", "2026-11-14") == [
        "2026-11-02", "2026-11-04", "2026-11-06",
        "2026-11-09", "2026-11-11", "2026-11-13",
    ]


def test_de_2_em_2_semanas():
    regra = Regra("semanal", d("2026-11-02"), intervalo=2, dias_semana=(1,))

    assert datas(regra, "2026-11-01", "2026-12-06") == [
        "2026-11-02", "2026-11-16", "2026-11-30",
    ]


def test_semanal_sem_dias_usa_o_dia_da_semana_do_inicio():
    regra = Regra("semanal", d("2026-11-04"))  # uma quarta-feira

    assert datas(regra, "2026-11-01", "2026-11-20") == [
        "2026-11-04", "2026-11-11", "2026-11-18",
    ]


def test_dias_da_primeira_semana_antes_do_inicio_ficam_de_fora():
    regra = Regra("semanal", d("2026-11-04"), dias_semana=(1, 3))  # segunda e quarta

    assert datas(regra, "2026-11-01", "2026-11-15") == [
        "2026-11-04", "2026-11-09", "2026-11-11",
    ]


def test_semanal_respeita_a_data_de_termino():
    regra = Regra("semanal", d("2026-11-02"), dias_semana=(1,), fim=d("2026-11-15"))

    assert datas(regra, "2026-11-01", "2026-12-31") == ["2026-11-02", "2026-11-09"]


def test_dias_da_semana_repetidos_sao_unificados():
    regra = Regra("semanal", d("2026-11-01"), dias_semana=(3, 3, 1))

    assert regra.dias_semana == (1, 3)


# ===== Mensal =====
def test_todo_dia_5():
    regra = Regra("mensal", d("2026-11-05"))

    assert datas(regra, "2026-11-01", "2027-02-28") == [
        "2026-11-05", "2026-12-05", "2027-01-05", "2027-02-05",
    ]


def test_dia_31_cai_no_ultimo_dia_dos_meses_mais_curtos():
    regra = Regra("mensal", d("2027-01-31"))

    assert datas(regra, "2027-01-01", "2027-04-30") == [
        "2027-01-31", "2027-02-28", "2027-03-31", "2027-04-30",
    ]


def test_dia_31_em_ano_bissexto():
    regra = Regra("mensal", d("2028-01-31"))

    assert "2028-02-29" in datas(regra, "2028-02-01", "2028-02-29")


def test_a_cada_2_meses():
    regra = Regra("mensal", d("2027-01-10"), intervalo=2)

    assert datas(regra, "2027-01-01", "2027-06-30") == [
        "2027-01-10", "2027-03-10", "2027-05-10",
    ]


def test_mensal_sem_dia_usa_o_dia_do_inicio():
    regra = Regra("mensal", d("2026-11-20"))

    assert datas(regra, "2026-11-01", "2026-12-31") == ["2026-11-20", "2026-12-20"]


def test_primeiro_mes_so_vale_depois_do_inicio():
    regra = Regra("mensal", d("2026-11-20"), dia_do_mes=5)

    assert datas(regra, "2026-11-01", "2027-01-31") == ["2026-12-05", "2027-01-05"]


def test_mensal_ate_data_de_termino():
    regra = Regra("mensal", d("2026-11-10"), fim=d("2027-01-09"))

    assert datas(regra, "2026-11-01", "2027-03-31") == ["2026-11-10", "2026-12-10"]


# ===== Regras e períodos inválidos =====
@pytest.mark.parametrize("intervalo", [0, -1, 366])
def test_intervalo_fora_dos_limites_e_recusado(intervalo):
    with pytest.raises(ValueError):
        Regra("diaria", d("2026-11-01"), intervalo=intervalo)


def test_frequencia_desconhecida_e_recusada():
    with pytest.raises(ValueError):
        Regra("anual", d("2026-11-01"))


def test_termino_antes_do_inicio_e_recusado():
    with pytest.raises(ValueError):
        Regra("diaria", d("2026-11-10"), fim=d("2026-11-09"))


@pytest.mark.parametrize("dia", [-1, 7])
def test_dia_da_semana_invalido_e_recusado(dia):
    with pytest.raises(ValueError):
        Regra("semanal", d("2026-11-01"), dias_semana=(dia,))


@pytest.mark.parametrize("dia", [0, 32])
def test_dia_do_mes_invalido_e_recusado(dia):
    with pytest.raises(ValueError):
        Regra("mensal", d("2026-11-01"), dia_do_mes=dia)


def test_periodo_invertido_e_recusado():
    with pytest.raises(ValueError):
        ocorrencias(Regra("diaria", d("2026-11-01")), d("2026-11-10"), d("2026-11-01"))


def test_periodo_grande_demais_e_recusado():
    with pytest.raises(ValueError):
        ocorrencias(Regra("diaria", d("2026-01-01")), d("2026-01-01"), d("2027-12-31"))