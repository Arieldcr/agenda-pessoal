"""Motor de datas das tarefas recorrentes.

São funções puras: recebem uma regra e um período e devolvem as datas.
Nada aqui lê ou grava no banco de dados.
"""

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta

FREQUENCIAS = ("diaria", "semanal", "mensal")
INTERVALO_MAXIMO = 365
PERIODO_MAXIMO_DIAS = 400


def dia_da_semana(dia: date) -> int:
    """0 = domingo, 1 = segunda, ... 6 = sábado (igual ao calendário da tela)."""
    return (dia.weekday() + 1) % 7


def domingo_da_semana(dia: date) -> date:
    """O domingo que abre a semana em que o dia está."""
    return dia - timedelta(days=dia_da_semana(dia))


@dataclass(frozen=True)
class Regra:
    """Quando uma atividade se repete.

    - diaria: de `intervalo` em `intervalo` dias, a partir do início.
    - semanal: nos `dias_semana` (0 a 6), de `intervalo` em `intervalo` semanas.
      Sem dias informados, usa o dia da semana do início.
    - mensal: no `dia_do_mes`, de `intervalo` em `intervalo` meses. Sem dia
      informado, usa o dia do início. Em meses mais curtos, cai no último dia.
    """

    frequencia: str
    inicio: date
    intervalo: int = 1
    fim: date | None = None
    dias_semana: tuple[int, ...] = ()
    dia_do_mes: int | None = None

    def __post_init__(self):
        if self.frequencia not in FREQUENCIAS:
            raise ValueError("Frequência inválida: use diaria, semanal ou mensal.")
        if not 1 <= self.intervalo <= INTERVALO_MAXIMO:
            raise ValueError(f"O intervalo deve ficar entre 1 e {INTERVALO_MAXIMO}.")
        if self.fim is not None and self.fim < self.inicio:
            raise ValueError("A data de término não pode ser anterior ao início.")
        if any(not 0 <= dia <= 6 for dia in self.dias_semana):
            raise ValueError("Os dias da semana vão de 0 (domingo) a 6 (sábado).")
        if self.dia_do_mes is not None and not 1 <= self.dia_do_mes <= 31:
            raise ValueError("O dia do mês deve ficar entre 1 e 31.")
        # A regra é imutável, então a normalização usa object.__setattr__.
        object.__setattr__(self, "dias_semana", tuple(sorted(set(self.dias_semana))))


def ocorrencias(regra: Regra, de: date, ate: date) -> list[date]:
    """Datas em que a regra cai dentro do período, de `de` até `ate` (inclusive)."""
    if ate < de:
        raise ValueError("O fim do período vem antes do início.")
    if (ate - de).days > PERIODO_MAXIMO_DIAS:
        raise ValueError(f"O período pode ter no máximo {PERIODO_MAXIMO_DIAS} dias.")

    primeiro = max(de, regra.inicio)
    ultimo = min(ate, regra.fim) if regra.fim else ate
    if primeiro > ultimo:
        return []

    if regra.frequencia == "diaria":
        return _diarias(regra, primeiro, ultimo)
    if regra.frequencia == "semanal":
        return _semanais(regra, primeiro, ultimo)
    return _mensais(regra, primeiro, ultimo)


def _diarias(regra: Regra, primeiro: date, ultimo: date) -> list[date]:
    passos = -(-(primeiro - regra.inicio).days // regra.intervalo)  # arredonda para cima
    dia = regra.inicio + timedelta(days=passos * regra.intervalo)
    datas = []
    while dia <= ultimo:
        datas.append(dia)
        dia += timedelta(days=regra.intervalo)
    return datas


def _semanais(regra: Regra, primeiro: date, ultimo: date) -> list[date]:
    dias = regra.dias_semana or (dia_da_semana(regra.inicio),)
    semana_inicial = domingo_da_semana(regra.inicio)
    datas = []
    dia = primeiro
    while dia <= ultimo:
        semanas = (domingo_da_semana(dia) - semana_inicial).days // 7
        if dia_da_semana(dia) in dias and semanas % regra.intervalo == 0:
            datas.append(dia)
        dia += timedelta(days=1)
    return datas


def _mensais(regra: Regra, primeiro: date, ultimo: date) -> list[date]:
    dia_pedido = regra.dia_do_mes or regra.inicio.day
    datas = []
    ano, mes = primeiro.year, primeiro.month
    while (ano, mes) <= (ultimo.year, ultimo.month):
        meses_desde_o_inicio = (ano - regra.inicio.year) * 12 + (mes - regra.inicio.month)
        if meses_desde_o_inicio % regra.intervalo == 0:
            dia = date(ano, mes, min(dia_pedido, monthrange(ano, mes)[1]))
            if primeiro <= dia <= ultimo:
                datas.append(dia)
        mes += 1
        if mes > 12:
            ano, mes = ano + 1, 1
    return datas