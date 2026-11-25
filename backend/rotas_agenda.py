"""Rota da agenda: tarefas avulsas e ocorrências de um período, no mesmo formato."""

from datetime import date, time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend import agenda

router = APIRouter()


class ItemAgenda(BaseModel):
    id: str
    tipo: str
    tarefa_id: int | None
    recorrencia_id: int | None
    data_original: date | None
    dia: date | None
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


@router.get("/agenda", response_model=list[ItemAgenda])
def consultar_agenda(de: date, ate: date, sem_dia: bool = False):
    try:
        return agenda.montar_agenda(de, ate, sem_dia)
    except ValueError as erro:
        raise HTTPException(status_code=422, detail=str(erro))