import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine

from backend import database
from backend.main import app


@pytest.fixture(autouse=True)
def banco_isolado(tmp_path, monkeypatch):
    """Troca o banco real por um arquivo temporário em TODOS os testes."""
    motor_teste = create_engine(
        f"sqlite:///{(tmp_path / 'teste.db').as_posix()}",
        connect_args={"check_same_thread": False},
    )
    monkeypatch.setattr(database, "engine", motor_teste)
    SQLModel.metadata.create_all(motor_teste)
    yield motor_teste
    motor_teste.dispose()


@pytest.fixture
def client(banco_isolado):
    """Cliente que faz pedidos à API sem ligar o servidor."""
    with TestClient(app) as cliente:
        yield cliente