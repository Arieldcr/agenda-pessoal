from datetime import date, time
from pathlib import Path

from sqlmodel import Field, Session, SQLModel, create_engine, select

# Pasta e arquivo do banco, sempre relativos à raiz do projeto.
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "agenda.db"

# Mude para True para ver no terminal o SQL que o SQLModel gera (útil para estudar).
MOSTRAR_SQL = False

# O "motor" é quem sabe se conectar ao banco.
engine = create_engine(
    f"sqlite:///{DB_PATH.as_posix()}",
    connect_args={"check_same_thread": False},
    echo=MOSTRAR_SQL,
)


class Tarefa(SQLModel, table=True):
    """Tabela de tarefas. Cada objeto Tarefa é uma linha da tabela."""

    id: int | None = Field(default=None, primary_key=True)
    titulo: str = Field(max_length=100)
    descricao: str | None = None
    concluida: bool = False
    dia: date | None = None
    hora: time | None = None
    duracao_min: int | None = None
    prioridade: str | None = None
    categoria: str | None = None


# Campos que o usuário pode alterar. O id nunca entra aqui.
CAMPOS_EDITAVEIS = {
    "titulo",
    "descricao",
    "concluida",
    "dia",
    "hora",
    "duracao_min",
    "prioridade",
    "categoria",
}

# Colunas acrescentadas depois da primeira versão da tabela.
COLUNAS_NOVAS = {
    "dia": "DATE",
    "hora": "TIME",
    "duracao_min": "INTEGER",
    "prioridade": "VARCHAR",
    "categoria": "VARCHAR",
}


def criar_tabelas() -> None:
    """Cria as tabelas que faltam e acrescenta as colunas novas nas tabelas antigas."""
    SQLModel.metadata.create_all(engine)
    _adicionar_colunas_novas()


def _adicionar_colunas_novas() -> None:
    """Migração simples: o create_all não altera tabelas que já existem."""
    with engine.begin() as conexao:
        colunas = {linha[1] for linha in conexao.exec_driver_sql("PRAGMA table_info(tarefa)")}
        for nome, tipo in COLUNAS_NOVAS.items():
            if nome not in colunas:
                conexao.exec_driver_sql(f"ALTER TABLE tarefa ADD COLUMN {nome} {tipo}")


def cadastrar_tarefa(
    titulo: str,
    descricao: str | None = None,
    dia: date | None = None,
    hora: time | None = None,
    duracao_min: int | None = None,
    prioridade: str | None = None,
    categoria: str | None = None,
) -> Tarefa:
    """Grava uma tarefa nova e a devolve já com o id gerado pelo banco."""
    tarefa = Tarefa(
        titulo=titulo,
        descricao=descricao,
        dia=dia,
        hora=hora,
        duracao_min=duracao_min,
        prioridade=prioridade,
        categoria=categoria,
    )
    with Session(engine) as sessao:
        sessao.add(tarefa)
        sessao.commit()
        sessao.refresh(tarefa)
    return tarefa


def listar_tarefas() -> list[Tarefa]:
    """Devolve todas as tarefas gravadas."""
    with Session(engine) as sessao:
        return list(sessao.exec(select(Tarefa)).all())


def buscar_tarefa(tarefa_id: int) -> Tarefa | None:
    """Devolve a tarefa com esse id, ou None se ela não existir."""
    with Session(engine) as sessao:
        return sessao.get(Tarefa, tarefa_id)


def atualizar_tarefa(tarefa_id: int, campos: dict) -> Tarefa | None:
    """Altera só os campos informados. Devolve None se a tarefa não existir."""
    with Session(engine) as sessao:
        tarefa = sessao.get(Tarefa, tarefa_id)
        if tarefa is None:
            return None
        for nome, valor in campos.items():
            if nome not in CAMPOS_EDITAVEIS:
                raise ValueError(f"Campo não editável: {nome}")
            setattr(tarefa, nome, valor)
        # Se alguma regra for quebrada, sai sem commit: nada é gravado.
        if tarefa.hora is not None and tarefa.dia is None:
            raise ValueError("A hora precisa de um dia: informe o dia junto com a hora.")
        if tarefa.duracao_min is not None and tarefa.hora is None:
            raise ValueError("A duração precisa de uma hora de início.")
        sessao.commit()
        sessao.refresh(tarefa)
        return tarefa


def excluir_tarefa(tarefa_id: int) -> bool:
    """Apaga a tarefa. Devolve True se apagou e False se ela não existia."""
    with Session(engine) as sessao:
        tarefa = sessao.get(Tarefa, tarefa_id)
        if tarefa is None:
            return False
        sessao.delete(tarefa)
        sessao.commit()
        return True