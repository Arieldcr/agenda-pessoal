"""Rotas das tarefas recorrentes: as regras e o estado de cada ocorrência."""

from datetime import date, time
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend import db_recorrencia
from backend.ocorrencias import montar_ocorrencia

router = APIRouter()

Prioridade = Literal["alta", "media", "baixa"]
Frequencia = Literal["diaria", "semanal", "mensal"]
StatusOcorrencia = Literal["pendente", "concluida", "cancelada"]


def categoria_vazia_vira_nula(valor):
    """Uma categoria só com espaços (ou vazia) é o mesmo que nenhuma categoria."""
    return valor or None


class RecorrenciaCriar(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    titulo: str = Field(min_length=1, max_length=100)
    descricao: str | None = None
    categoria: str | None = Field(default=None, max_length=30)
    prioridade: Prioridade | None = None
    hora: time | None = None
    duracao_min: int | None = Field(default=None, ge=1, le=1440)
    frequencia: Frequencia
    intervalo: int = Field(default=1, ge=1, le=365)
    dias_semana: list[int] | None = None
    dia_do_mes: int | None = Field(default=None, ge=1, le=31)
    inicio: date
    fim: date | None = None

    _limpar_categoria = field_validator("categoria")(categoria_vazia_vira_nula)


class RecorrenciaAtualizar(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    titulo: str | None = Field(default=None, min_length=1, max_length=100)
    descricao: str | None = None
    categoria: str | None = Field(default=None, max_length=30)
    prioridade: Prioridade | None = None
    hora: time | None = None
    duracao_min: int | None = Field(default=None, ge=1, le=1440)
    frequencia: Frequencia | None = None
    intervalo: int | None = Field(default=None, ge=1, le=365)
    dias_semana: list[int] | None = None
    dia_do_mes: int | None = Field(default=None, ge=1, le=31)
    inicio: date | None = None
    fim: date | None = None

    _limpar_categoria = field_validator("categoria")(categoria_vazia_vira_nula)

    @field_validator("titulo", "frequencia", "intervalo", "inicio")
    @classmethod
    def nao_aceitar_nulo(cls, valor):
        if valor is None:
            raise ValueError("não pode ser nulo; omita o campo para não alterá-lo")
        return valor


class OcorrenciaAtualizar(BaseModel):
    """Estado de uma ocorrência. Enviar null em um campo volta ao valor da regra."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    status: StatusOcorrencia | None = None
    dia: date | None = None
    hora: time | None = None
    titulo: str | None = Field(default=None, min_length=1, max_length=100)
    descricao: str | None = None
    categoria: str | None = Field(default=None, max_length=30)
    prioridade: Prioridade | None = None
    duracao_min: int | None = Field(default=None, ge=1, le=1440)

    _limpar_categoria = field_validator("categoria")(categoria_vazia_vira_nula)

    @field_validator("status")
    @classmethod
    def status_nao_aceita_nulo(cls, valor):
        if valor is None:
            raise ValueError("não pode ser nulo; omita o campo para não alterá-lo")
        return valor


class RecorrenciaResposta(BaseModel):
    id: int
    titulo: str
    descricao: str | None
    categoria: str | None
    prioridade: str | None
    hora: time | None
    duracao_min: int | None
    frequencia: str
    intervalo: int
    dias_semana: list[int]
    dia_do_mes: int | None
    inicio: date
    fim: date | None


class OcorrenciaResposta(BaseModel):
    id: str
    tipo: str
    recorrencia_id: int
    data_original: date
    dia: date
    hora: time | None
    titulo: str
    descricao: str | None
    categoria: str | None
    prioridade: str | None
    duracao_min: int | None
    status: str
    concluida: bool
    remarcada: bool
    alterada: bool


def resposta_da_recorrencia(recorrencia) -> RecorrenciaResposta:
    dados = recorrencia.model_dump()
    dados["dias_semana"] = db_recorrencia.dias_da_recorrencia(recorrencia)
    return RecorrenciaResposta(**dados)


@router.post("/recorrencias", response_model=RecorrenciaResposta, status_code=201)
def cadastrar_recorrencia(dados: RecorrenciaCriar):
    try:
        recorrencia = db_recorrencia.cadastrar_recorrencia(dados.model_dump())
    except ValueError as erro:
        raise HTTPException(status_code=422, detail=str(erro))
    return resposta_da_recorrencia(recorrencia)


@router.get("/recorrencias", response_model=list[RecorrenciaResposta])
def listar_recorrencias():
    return [resposta_da_recorrencia(r) for r in db_recorrencia.listar_recorrencias()]


@router.get("/recorrencias/{recorrencia_id}", response_model=RecorrenciaResposta)
def buscar_recorrencia(recorrencia_id: int):
    recorrencia = db_recorrencia.buscar_recorrencia(recorrencia_id)
    if recorrencia is None:
        raise HTTPException(status_code=404, detail="Recorrência não encontrada")
    return resposta_da_recorrencia(recorrencia)


@router.patch("/recorrencias/{recorrencia_id}", response_model=RecorrenciaResposta)
def atualizar_recorrencia(recorrencia_id: int, dados: RecorrenciaAtualizar):
    campos = dados.model_dump(exclude_unset=True)
    try:
        recorrencia = db_recorrencia.atualizar_recorrencia(recorrencia_id, campos)
    except ValueError as erro:
        raise HTTPException(status_code=422, detail=str(erro))
    if recorrencia is None:
        raise HTTPException(status_code=404, detail="Recorrência não encontrada")
    return resposta_da_recorrencia(recorrencia)


@router.delete("/recorrencias/{recorrencia_id}", status_code=204)
def excluir_recorrencia(recorrencia_id: int):
    if not db_recorrencia.excluir_recorrencia(recorrencia_id):
        raise HTTPException(status_code=404, detail="Recorrência não encontrada")


@router.put(
    "/recorrencias/{recorrencia_id}/ocorrencias/{dia}", response_model=OcorrenciaResposta
)
def salvar_ocorrencia(recorrencia_id: int, dia: date, dados: OcorrenciaAtualizar):
    campos = dados.model_dump(exclude_unset=True)
    try:
        resultado = db_recorrencia.salvar_ocorrencia(recorrencia_id, dia, campos)
    except ValueError as erro:
        raise HTTPException(status_code=422, detail=str(erro))
    if resultado is None:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada")
    recorrencia, excecao = resultado
    return montar_ocorrencia(recorrencia, excecao, dia)


@router.delete("/recorrencias/{recorrencia_id}/ocorrencias/{dia}", status_code=204)
def voltar_ocorrencia_ao_padrao(recorrencia_id: int, dia: date):
    if not db_recorrencia.excluir_ocorrencia(recorrencia_id, dia):
        raise HTTPException(status_code=404, detail="Ocorrência sem alterações")