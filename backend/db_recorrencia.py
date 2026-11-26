"""Tabelas e operações das tarefas recorrentes: a regra e o estado de cada ocorrência."""

from datetime import date, time, timedelta

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Session, SQLModel, select

from backend import database
from backend.recorrencia import PERIODO_MAXIMO_DIAS, Regra, ocorrencias


class Recorrencia(SQLModel, table=True):
    """A regra de repetição. As ocorrências são calculadas e não ficam gravadas."""

    id: int | None = Field(default=None, primary_key=True)
    titulo: str = Field(max_length=100)
    descricao: str | None = None
    categoria: str | None = None
    prioridade: str | None = None
    hora: time | None = None
    duracao_min: int | None = None
    frequencia: str
    intervalo: int = 1
    dias_semana: str | None = None  # texto como "1,3,5" (0 = domingo)
    dia_do_mes: int | None = None
    inicio: date
    fim: date | None = None


class Ocorrencia(SQLModel, table=True):
    """Estado próprio de UMA ocorrência. Só existe quando algo nela foi alterado.

    A identidade é o par (recorrencia_id, data_original), que não se repete.
    Campos vazios significam "usa o valor da regra".
    """

    __table_args__ = (UniqueConstraint("recorrencia_id", "data_original"),)

    id: int | None = Field(default=None, primary_key=True)
    recorrencia_id: int = Field(foreign_key="recorrencia.id", index=True)
    data_original: date
    status: str = "pendente"  # pendente, concluida ou cancelada
    dia: date | None = None  # preenchido quando a ocorrência foi remarcada
    hora: time | None = None
    titulo: str | None = None
    descricao: str | None = None
    categoria: str | None = None
    prioridade: str | None = None
    duracao_min: int | None = None


CAMPOS_RECORRENCIA = {
    "titulo", "descricao", "categoria", "prioridade", "hora", "duracao_min",
    "frequencia", "intervalo", "dias_semana", "dia_do_mes", "inicio", "fim",
}
CAMPOS_OCORRENCIA = {
    "status", "dia", "hora", "titulo", "descricao", "categoria", "prioridade", "duracao_min",
}


def dias_da_recorrencia(recorrencia: Recorrencia) -> list[int]:
    if not recorrencia.dias_semana:
        return []
    return [int(parte) for parte in recorrencia.dias_semana.split(",")]


def regra_da_recorrencia(recorrencia: Recorrencia) -> Regra:
    return Regra(
        frequencia=recorrencia.frequencia,
        inicio=recorrencia.inicio,
        intervalo=recorrencia.intervalo,
        fim=recorrencia.fim,
        dias_semana=tuple(dias_da_recorrencia(recorrencia)),
        dia_do_mes=recorrencia.dia_do_mes,
    )


def _dias_como_texto(campos: dict) -> dict:
    campos = dict(campos)
    if isinstance(campos.get("dias_semana"), list):
        campos["dias_semana"] = ",".join(str(dia) for dia in campos["dias_semana"]) or None
    return campos


def _preparar_recorrencia(recorrencia: Recorrencia) -> None:
    """Descarta o que não vale para a frequência e confere todas as regras."""
    if recorrencia.frequencia != "semanal":
        recorrencia.dias_semana = None
    if recorrencia.frequencia != "mensal":
        recorrencia.dia_do_mes = None
    if recorrencia.duracao_min is not None and recorrencia.hora is None:
        raise ValueError("A duração precisa de uma hora de início.")
    regra = regra_da_recorrencia(recorrencia)  # recusa frequência, intervalo, datas e dias inválidos
    recorrencia.dias_semana = ",".join(str(dia) for dia in regra.dias_semana) or None


def cadastrar_recorrencia(campos: dict) -> Recorrencia:
    recorrencia = Recorrencia(**_dias_como_texto(campos))
    _preparar_recorrencia(recorrencia)
    with Session(database.engine) as sessao:
        sessao.add(recorrencia)
        sessao.commit()
        sessao.refresh(recorrencia)
    return recorrencia


def listar_recorrencias() -> list[Recorrencia]:
    with Session(database.engine) as sessao:
        return list(sessao.exec(select(Recorrencia)).all())


def buscar_recorrencia(recorrencia_id: int) -> Recorrencia | None:
    with Session(database.engine) as sessao:
        return sessao.get(Recorrencia, recorrencia_id)


def atualizar_recorrencia(recorrencia_id: int, campos: dict) -> Recorrencia | None:
    with Session(database.engine) as sessao:
        recorrencia = sessao.get(Recorrencia, recorrencia_id)
        if recorrencia is None:
            return None
        for nome, valor in _dias_como_texto(campos).items():
            if nome not in CAMPOS_RECORRENCIA:
                raise ValueError(f"Campo não editável: {nome}")
            setattr(recorrencia, nome, valor)
        _preparar_recorrencia(recorrencia)  # se algo for inválido, sai sem commit
        sessao.commit()
        sessao.refresh(recorrencia)
        return recorrencia


def excluir_recorrencia(recorrencia_id: int) -> bool:
    """Apaga a regra e o estado de todas as suas ocorrências."""
    with Session(database.engine) as sessao:
        recorrencia = sessao.get(Recorrencia, recorrencia_id)
        if recorrencia is None:
            return False
        excecoes = sessao.exec(
            select(Ocorrencia).where(Ocorrencia.recorrencia_id == recorrencia_id)
        ).all()
        for excecao in excecoes:
            sessao.delete(excecao)
        sessao.delete(recorrencia)
        sessao.commit()
        return True


def _buscar_excecao(sessao: Session, recorrencia_id: int, dia_original: date):
    return sessao.exec(
        select(Ocorrencia).where(
            Ocorrencia.recorrencia_id == recorrencia_id,
            Ocorrencia.data_original == dia_original,
        )
    ).first()


def salvar_ocorrencia(recorrencia_id: int, dia_original: date, campos: dict):
    """Cria ou atualiza o estado de uma ocorrência (repetir o pedido não duplica).

    Devolve (recorrencia, ocorrencia), ou None se a regra não existe ou se a data
    não é uma ocorrência dela.
    """
    with Session(database.engine) as sessao:
        recorrencia = sessao.get(Recorrencia, recorrencia_id)
        if recorrencia is None:
            return None
        regra = regra_da_recorrencia(recorrencia)
        if dia_original not in ocorrencias(regra, dia_original, dia_original):
            return None

        excecao = _buscar_excecao(sessao, recorrencia_id, dia_original)
        if excecao is None:
            excecao = Ocorrencia(recorrencia_id=recorrencia_id, data_original=dia_original)
        for nome, valor in campos.items():
            if nome not in CAMPOS_OCORRENCIA:
                raise ValueError(f"Campo não editável: {nome}")
            setattr(excecao, nome, valor)

        hora = excecao.hora if excecao.hora is not None else recorrencia.hora
        duracao = excecao.duracao_min if excecao.duracao_min is not None else recorrencia.duracao_min
        if duracao is not None and hora is None:
            raise ValueError("A duração precisa de uma hora de início.")

        sessao.add(excecao)
        sessao.commit()
        sessao.refresh(excecao)
        sessao.refresh(recorrencia)
        return recorrencia, excecao


def excluir_ocorrencia(recorrencia_id: int, dia_original: date) -> bool:
    """Volta a ocorrência ao padrão da regra. False se ela não tinha estado próprio."""
    with Session(database.engine) as sessao:
        excecao = _buscar_excecao(sessao, recorrencia_id, dia_original)
        if excecao is None:
            return False
        sessao.delete(excecao)
        sessao.commit()
        return True



def _ha_ocorrencia_antes(regra: Regra, dia: date) -> bool:
    """Existe alguma ocorrência da regra antes de `dia`?"""
    fim = dia - timedelta(days=1)
    while fim >= regra.inicio:
        inicio = max(regra.inicio, fim - timedelta(days=PERIODO_MAXIMO_DIAS))
        if ocorrencias(regra, inicio, fim):
            return True
        fim = inicio - timedelta(days=1)
    return False


def _estados_a_partir_de(sessao: Session, recorrencia_id: int, dia: date) -> list[Ocorrencia]:
    return list(
        sessao.exec(
            select(Ocorrencia).where(
                Ocorrencia.recorrencia_id == recorrencia_id,
                Ocorrencia.data_original >= dia,
            )
        ).all()
    )


def dividir_recorrencia(recorrencia_id: int, a_partir_de: date, campos: dict) -> Recorrencia | None:
    """Altera esta ocorrência e as próximas.

    A regra antiga termina na véspera e uma regra nova, com as mudanças, começa em
    `a_partir_de`. O estado das datas seguintes que continuam existindo passa para a
    regra nova. Se nada vem antes, é o mesmo que alterar a regra inteira.
    Devolve None se a regra não existe ou se a data não é uma ocorrência dela.
    """
    with Session(database.engine) as sessao:
        antiga = sessao.get(Recorrencia, recorrencia_id)
        if antiga is None:
            return None
        regra_antiga = regra_da_recorrencia(antiga)
        if a_partir_de not in ocorrencias(regra_antiga, a_partir_de, a_partir_de):
            return None
        campos = _dias_como_texto(campos)
        for nome in campos:
            if nome not in CAMPOS_RECORRENCIA:
                raise ValueError(f"Campo não editável: {nome}")

        if not _ha_ocorrencia_antes(regra_antiga, a_partir_de):
            for nome, valor in campos.items():
                setattr(antiga, nome, valor)
            _preparar_recorrencia(antiga)
            sessao.commit()
            sessao.refresh(antiga)
            return antiga

        dados = {nome: getattr(antiga, nome) for nome in CAMPOS_RECORRENCIA}
        dados["inicio"] = a_partir_de
        dados.update(campos)
        if dados["inicio"] < a_partir_de:
            raise ValueError("A nova série não pode começar antes desta ocorrência.")
        nova = Recorrencia(**dados)
        _preparar_recorrencia(nova)  # confere tudo antes de mexer na regra antiga

        antiga.fim = a_partir_de - timedelta(days=1)
        sessao.add(nova)
        sessao.flush()  # gera o id da regra nova
        regra_nova = regra_da_recorrencia(nova)
        for estado in _estados_a_partir_de(sessao, antiga.id, a_partir_de):
            if estado.data_original in ocorrencias(regra_nova, estado.data_original, estado.data_original):
                estado.recorrencia_id = nova.id
            else:
                sessao.delete(estado)
        sessao.commit()
        sessao.refresh(nova)
        return nova


def encerrar_a_partir_de(recorrencia_id: int, a_partir_de: date) -> bool:
    """Exclui esta ocorrência e as próximas. False se a data não é uma ocorrência."""
    with Session(database.engine) as sessao:
        recorrencia = sessao.get(Recorrencia, recorrencia_id)
        if recorrencia is None:
            return False
        regra = regra_da_recorrencia(recorrencia)
        if a_partir_de not in ocorrencias(regra, a_partir_de, a_partir_de):
            return False

        if _ha_ocorrencia_antes(regra, a_partir_de):
            for estado in _estados_a_partir_de(sessao, recorrencia_id, a_partir_de):
                sessao.delete(estado)
            recorrencia.fim = a_partir_de - timedelta(days=1)
        else:
            estados = sessao.exec(
                select(Ocorrencia).where(Ocorrencia.recorrencia_id == recorrencia_id)
            ).all()
            for estado in estados:
                sessao.delete(estado)
            sessao.delete(recorrencia)
        sessao.commit()
        return True  