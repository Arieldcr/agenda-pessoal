from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from backend import database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Roda uma vez, quando o servidor liga: garante que as tabelas existem.
    database.criar_tabelas()
    yield


app = FastAPI(title="Assistente de Agenda Pessoal", lifespan=lifespan)


class TarefaCriar(BaseModel):
    """Dados que o usuário envia para cadastrar uma tarefa."""

    model_config = ConfigDict(str_strip_whitespace=True)

    titulo: str = Field(min_length=1, max_length=100)
    descricao: str | None = None


@app.get("/")
def raiz():
    return {"mensagem": "Assistente de Agenda Pessoal funcionando"}


@app.post("/tarefas", response_model=database.Tarefa, status_code=201)
def cadastrar_tarefa(dados: TarefaCriar):
    return database.cadastrar_tarefa(dados.titulo, dados.descricao)


@app.get("/tarefas", response_model=list[database.Tarefa])
def listar_tarefas():
    return database.listar_tarefas()


@app.get("/tarefas/{tarefa_id}", response_model=database.Tarefa)
def buscar_tarefa(tarefa_id: int):
    tarefa = database.buscar_tarefa(tarefa_id)
    if tarefa is None:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return tarefa