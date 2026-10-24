from pathlib import Path

from sqlmodel import Field, Session, SQLModel, create_engine, select

# Pasta e arquivo do banco, sempre relativos à raiz do projeto.
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "agenda.db"

# O "motor" é quem sabe se conectar ao banco.
# echo=True mostra no terminal o SQL que o SQLModel gera (útil para aprender).
engine = create_engine(
    f"sqlite:///{DB_PATH.as_posix()}",
    connect_args={"check_same_thread": False},
    echo=True,
)


class Tarefa(SQLModel, table=True):
    """Tabela de tarefas. Cada objeto Tarefa é uma linha da tabela."""

    id: int | None = Field(default=None, primary_key=True)
    titulo: str = Field(max_length=100)
    descricao: str | None = None
    concluida: bool = False


def criar_tabelas() -> None:
    """Cria as tabelas no banco, se ainda não existirem."""
    SQLModel.metadata.create_all(engine)


def cadastrar_tarefa(titulo: str, descricao: str | None = None) -> Tarefa:
    """Grava uma tarefa nova e a devolve já com o id gerado pelo banco."""
    tarefa = Tarefa(titulo=titulo, descricao=descricao)
    with Session(engine) as sessao:
        sessao.add(tarefa)
        sessao.commit()
        sessao.refresh(tarefa)
    return tarefa


def listar_tarefas() -> list[Tarefa]:
    """Devolve todas as tarefas gravadas."""
    with Session(engine) as sessao:
        return list(sessao.exec(select(Tarefa)).all())