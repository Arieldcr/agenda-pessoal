"""Junta a regra de uma recorrência com o estado próprio de uma ocorrência."""

from datetime import date

CAMPOS_SOBRESCRITOS = ("dia", "hora", "titulo", "descricao", "categoria", "prioridade", "duracao_min")


def montar_ocorrencia(recorrencia, excecao, dia_original: date) -> dict:
    """Devolve a ocorrência no formato que a tela vai usar, como se fosse uma tarefa."""

    def valor(nome):
        sobrescrito = getattr(excecao, nome) if excecao is not None else None
        return sobrescrito if sobrescrito is not None else getattr(recorrencia, nome)

    status = excecao.status if excecao is not None else "pendente"
    dia = excecao.dia if excecao is not None and excecao.dia is not None else dia_original
    alterada = excecao is not None and any(
        getattr(excecao, nome) is not None for nome in CAMPOS_SOBRESCRITOS
    )
    return {
        "id": f"r{recorrencia.id}-{dia_original.isoformat()}",
        "tipo": "recorrente",
        "recorrencia_id": recorrencia.id,
        "data_original": dia_original,
        "dia": dia,
        "hora": valor("hora"),
        "titulo": valor("titulo"),
        "descricao": valor("descricao"),
        "categoria": valor("categoria"),
        "prioridade": valor("prioridade"),
        "duracao_min": valor("duracao_min"),
        "status": status,
        "concluida": status == "concluida",
        "remarcada": dia != dia_original,
        "alterada": alterada,
    }