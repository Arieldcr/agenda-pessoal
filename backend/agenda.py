"""Agenda por período: reúne as tarefas avulsas e as ocorrências das recorrências.

Nada de futuro é gravado: as ocorrências são calculadas a partir das regras e
combinadas com o estado próprio de cada data (concluída, cancelada, remarcada...).
"""

from datetime import date, time

from sqlalchemy import and_, or_
from sqlmodel import Session, col, select

from backend import database
from backend.db_recorrencia import Ocorrencia, Recorrencia, regra_da_recorrencia
from backend.ocorrencias import montar_ocorrencia
from backend.recorrencia import PERIODO_MAXIMO_DIAS, ocorrencias


def item_da_tarefa(tarefa) -> dict:
    """Uma tarefa avulsa no mesmo formato das ocorrências."""
    return {
        "id": f"t{tarefa.id}",
        "tipo": "tarefa",
        "tarefa_id": tarefa.id,
        "recorrencia_id": None,
        "data_original": None,
        "dia": tarefa.dia,
        "hora": tarefa.hora,
        "titulo": tarefa.titulo,
        "descricao": tarefa.descricao,
        "categoria": tarefa.categoria,
        "prioridade": tarefa.prioridade,
        "duracao_min": tarefa.duracao_min,
        "status": "concluida" if tarefa.concluida else "pendente",
        "concluida": tarefa.concluida,
        "remarcada": False,
        "alterada": False,
    }


def _chave_de_ordem(item: dict):
    return (
        item["dia"] or date.max,
        item["hora"] is None,
        item["hora"] or time.min,
        item["id"],
    )


def montar_agenda(de: date, ate: date, incluir_sem_dia: bool = False) -> list[dict]:
    """Tudo o que cai entre `de` e `ate` (inclusive), ordenado por dia e hora."""
    if ate < de:
        raise ValueError("O fim do período vem antes do início.")
    if (ate - de).days > PERIODO_MAXIMO_DIAS:
        raise ValueError(f"O período pode ter no máximo {PERIODO_MAXIMO_DIAS} dias.")

    itens = []
    with Session(database.engine) as sessao:
        tarefas_no_periodo = and_(col(database.Tarefa.dia) >= de, col(database.Tarefa.dia) <= ate)
        if incluir_sem_dia:
            tarefas_no_periodo = or_(tarefas_no_periodo, col(database.Tarefa.dia).is_(None))
        tarefas = sessao.exec(select(database.Tarefa).where(tarefas_no_periodo)).all()
        itens.extend(item_da_tarefa(tarefa) for tarefa in tarefas)

        # Estados próprios que tocam o período: pela data original ou pela data nova.
        estados = sessao.exec(
            select(Ocorrencia).where(
                or_(
                    and_(col(Ocorrencia.data_original) >= de, col(Ocorrencia.data_original) <= ate),
                    and_(col(Ocorrencia.dia) >= de, col(Ocorrencia.dia) <= ate),
                )
            )
        ).all()
        estados_por_regra: dict[int, dict[date, Ocorrencia]] = {}
        for estado in estados:
            estados_por_regra.setdefault(estado.recorrencia_id, {})[estado.data_original] = estado

        for recorrencia in sessao.exec(select(Recorrencia)).all():
            regra = regra_da_recorrencia(recorrencia)
            do_periodo = estados_por_regra.get(recorrencia.id, {})
            # Estado de uma data que a regra não gera mais (regra editada) é ignorado.
            validos = {dia for dia in do_periodo if dia in ocorrencias(regra, dia, dia)}
            for original in set(ocorrencias(regra, de, ate)) | validos:
                item = montar_ocorrencia(recorrencia, do_periodo.get(original), original)
                if item["status"] == "cancelada" or not de <= item["dia"] <= ate:
                    continue
                item["tarefa_id"] = None
                itens.append(item)

    itens.sort(key=_chave_de_ordem)
    return itens