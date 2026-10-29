from pathlib import Path

from backend import database


def test_testes_nao_usam_o_banco_real():
    caminho_em_uso = Path(database.engine.url.database).resolve()
    assert caminho_em_uso != database.DB_PATH.resolve()
    assert caminho_em_uso.name == "teste.db"