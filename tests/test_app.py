from dataclasses import dataclass, field
from typing import Any

import pytest
from fastapi.testclient import TestClient

import app as app_module

client = TestClient(app_module.app)


@dataclass
class FakeCursor:
    one: dict[str, Any] | None = None
    many: list[dict[str, Any]] = field(default_factory=list)
    rowcount: int = 1
    lastrowid: int = 7
    statements: list[tuple[str, tuple[Any, ...] | None]] = field(default_factory=list)
    closed: bool = False

    def execute(self, sql: str, values: tuple[Any, ...] | None = None):
        self.statements.append((sql, values))

    def fetchone(self):
        return self.one

    def fetchall(self):
        return self.many

    def close(self):
        self.closed = True


@dataclass
class FakeConnection:
    fake_cursor: FakeCursor
    committed: bool = False
    closed: bool = False

    def cursor(self, dictionary: bool = False):
        return self.fake_cursor

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True


@pytest.fixture
def fake_database(monkeypatch):
    cursor = FakeCursor()
    connection = FakeConnection(cursor)
    monkeypatch.setattr(app_module, "conectar_banco", lambda: connection)
    return cursor, connection


def test_home_informa_que_api_esta_ativa():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Customer Management API is running!"}


def test_cliente_invalido_retorna_422():
    response = client.post(
        "/clientes",
        json={"nome": "A", "email": "email-invalido", "idade": 150},
    )

    assert response.status_code == 422


def test_busca_de_cliente_inexistente_retorna_404(fake_database):
    response = client.get("/clientes/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Cliente não encontrado"}


def test_lista_clientes(fake_database):
    cursor, _ = fake_database
    cursor.many = [{"id": 1, "nome": "Ana", "email": "ana@example.com", "idade": 28}]

    response = client.get("/clientes")

    assert response.status_code == 200
    assert response.json()[0]["nome"] == "Ana"


def test_busca_cliente_existente(fake_database):
    cursor, _ = fake_database
    cursor.one = {"id": 1, "nome": "Ana", "email": "ana@example.com", "idade": 28}

    response = client.get("/clientes/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_cadastro_persiste_cliente(fake_database):
    cursor, connection = fake_database

    response = client.post(
        "/clientes",
        json={"nome": "Otavio Moretti", "email": "OTAVIO@EXAMPLE.COM", "idade": 30},
    )

    assert response.status_code == 201
    assert response.json()["id"] == 7
    assert response.json()["cliente"]["email"] == "otavio@example.com"
    assert "INSERT INTO clientes" in cursor.statements[0][0]
    assert connection.committed is True
    assert cursor.closed is True
    assert connection.closed is True


def test_atualiza_cliente_existente(fake_database):
    cursor, connection = fake_database
    cursor.one = {"id": 1}

    response = client.put(
        "/clientes/1",
        json={"nome": "Ana Lima", "email": "ana@example.com", "idade": 29},
    )

    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert "UPDATE clientes" in cursor.statements[1][0]
    assert connection.committed is True


def test_atualizacao_de_cliente_inexistente_retorna_404(fake_database):
    response = client.put(
        "/clientes/999",
        json={"nome": "Ana Lima", "email": "ana@example.com", "idade": 29},
    )

    assert response.status_code == 404


def test_exclui_cliente_existente(fake_database):
    _, connection = fake_database

    response = client.delete("/clientes/1")

    assert response.status_code == 200
    assert response.json() == {"message": "Cliente excluído com sucesso!"}
    assert connection.committed is True


def test_exclusao_de_cliente_inexistente_retorna_404(fake_database):
    cursor, _ = fake_database
    cursor.rowcount = 0

    response = client.delete("/clientes/999")

    assert response.status_code == 404
