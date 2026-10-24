from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(title="Assistente de Agenda Pessoal")


class TarefaCriar(BaseModel):
    """Dados que o usuário envia para cadastrar uma tarefa."""

    model_config = ConfigDict(str_strip_whitespace=True)

    titulo: str = Field(min_length=1, max_length=100)
    descricao: str | None = None


class Tarefa(BaseModel):
    """Tarefa completa, como o sistema a guarda e devolve."""

    id: int
    titulo: str
    descricao: str | None = None
    concluida: bool = False


# Armazenamento temporário, na memória.
# Será substituído pelo SQLite no Passo 2B.
tarefas: list[Tarefa] = []
proximo_id = 1


@app.get("/")
def raiz():
    return {"mensagem": "Assistente de Agenda Pessoal funcionando"}


@app.post("/tarefas", response_model=Tarefa, status_code=201)
def cadastrar_tarefa(dados: TarefaCriar):
    global proximo_id
    tarefa = Tarefa(id=proximo_id, titulo=dados.titulo, descricao=dados.descricao)
    proximo_id += 1
    tarefas.append(tarefa)
    return tarefa


@app.get("/tarefas", response_model=list[Tarefa])
def listar_tarefas():
    return tarefas