from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

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


class TarefaAtualizar(BaseModel):
    """Campos que podem ser alterados. Todos são opcionais: só o que for enviado muda."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    titulo: str | None = Field(default=None, min_length=1, max_length=100)
    descricao: str | None = None
    concluida: bool | None = None

    @field_validator("titulo", "concluida")
    @classmethod
    def nao_aceitar_nulo(cls, valor):
        if valor is None:
            raise ValueError("não pode ser nulo; omita o campo para não alterá-lo")
        return valor


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


@app.patch("/tarefas/{tarefa_id}", response_model=database.Tarefa)
def atualizar_tarefa(tarefa_id: int, dados: TarefaAtualizar):
    campos = dados.model_dump(exclude_unset=True)
    tarefa = database.atualizar_tarefa(tarefa_id, campos)
    if tarefa is None:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return tarefa


@app.delete("/tarefas/{tarefa_id}", status_code=204)
def excluir_tarefa(tarefa_id: int):
    if not database.excluir_tarefa(tarefa_id):
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")