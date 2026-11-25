from contextlib import asynccontextmanager
from datetime import date, time
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend import database, rotas_agenda, rotas_recorrencia

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Roda uma vez, quando o servidor liga: garante que as tabelas existem.
    database.criar_tabelas()
    yield


app = FastAPI(title="Assistente de Agenda Pessoal", lifespan=lifespan)

Prioridade = Literal["alta", "media", "baixa"]


def categoria_vazia_vira_nula(valor):
    """Uma categoria só com espaços (ou vazia) é o mesmo que nenhuma categoria."""
    return valor or None


class TarefaCriar(BaseModel):
    """Dados que o usuário envia para cadastrar uma tarefa."""

    model_config = ConfigDict(str_strip_whitespace=True)

    titulo: str = Field(min_length=1, max_length=100)
    descricao: str | None = None
    dia: date | None = None
    hora: time | None = None
    duracao_min: int | None = Field(default=None, ge=1, le=1440)
    prioridade: Prioridade | None = None
    categoria: str | None = Field(default=None, max_length=30)

    _limpar_categoria = field_validator("categoria")(categoria_vazia_vira_nula)

    @model_validator(mode="after")
    def conferir_regras_de_prazo(self):
        if self.hora is not None and self.dia is None:
            raise ValueError("a hora precisa de um dia: informe o dia junto com a hora")
        if self.duracao_min is not None and self.hora is None:
            raise ValueError("a duração precisa de uma hora de início")
        return self


class TarefaAtualizar(BaseModel):
    """Campos que podem ser alterados. Todos são opcionais: só o que for enviado muda."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    titulo: str | None = Field(default=None, min_length=1, max_length=100)
    descricao: str | None = None
    concluida: bool | None = None
    dia: date | None = None
    hora: time | None = None
    duracao_min: int | None = Field(default=None, ge=1, le=1440)
    prioridade: Prioridade | None = None
    categoria: str | None = Field(default=None, max_length=30)

    _limpar_categoria = field_validator("categoria")(categoria_vazia_vira_nula)

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
    return database.cadastrar_tarefa(
        dados.titulo,
        dados.descricao,
        dados.dia,
        dados.hora,
        dados.duracao_min,
        dados.prioridade,
        dados.categoria,
    )


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
    try:
        tarefa = database.atualizar_tarefa(tarefa_id, campos)
    except ValueError as erro:
        raise HTTPException(status_code=422, detail=str(erro))
    if tarefa is None:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return tarefa


@app.delete("/tarefas/{tarefa_id}", status_code=204)
def excluir_tarefa(tarefa_id: int):
    if not database.excluir_tarefa(tarefa_id):
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    
app.include_router(rotas_recorrencia.router)
app.include_router(rotas_agenda.router)
# O frontend (HTML, CSS e JavaScript) é entregue em /app/.
# O mount fica por último, para não interferir nas rotas da API.
PASTA_FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/app", StaticFiles(directory=PASTA_FRONTEND, html=True), name="frontend")