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
    rolled_back: bool = False

    def cursor(self, dictionary: bool = False):
        return self.fake_cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

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


@pytest.mark.parametrize("metodo,rota", [("post", "/clientes"), ("put", "/clientes/1")])
@pytest.mark.parametrize(
    "campo,valor",
    [
        ("nome", "  "),
        ("nome", "\t\n"),
        ("nome", " A "),
        ("nome", "A" * 101),
        ("nome", None),
        ("email", "@example.com"),
        ("email", "ana@@example.com"),
        ("email", "ana lima@example.com"),
        ("email", "ana@example..com"),
        ("email", "ana@.com"),
        ("email", "a" * 64 + "@" + "b" * 63 + "." + "c" * 20 + ".com"),
    ],
)
def test_entrada_invalida_nao_acessa_banco(monkeypatch, metodo, rota, campo, valor):
    def banco_nao_deve_ser_acessado():
        pytest.fail("Entrada inválida não deve abrir conexão com o banco")

    monkeypatch.setattr(app_module, "conectar_banco", banco_nao_deve_ser_acessado)
    dados = {"nome": "Ana Lima", "email": "ana@example.com", "idade": 28}
    dados[campo] = valor

    response = getattr(client, metodo)(rota, json=dados)

    assert response.status_code == 422
    assert any(erro["loc"][-1] == campo for erro in response.json()["detail"])


@pytest.mark.parametrize("metodo,rota", [("post", "/clientes"), ("put", "/clientes/1")])
def test_persiste_nome_e_email_normalizados(fake_database, metodo, rota):
    cursor, connection = fake_database
    cursor.one = {"id": 1}

    response = getattr(client, metodo)(
        rota,
        json={"nome": "  Ana Lima  ", "email": " ANA+FESTA@EXAMPLE.COM ", "idade": 28},
    )

    assert response.status_code == (201 if metodo == "post" else 200)
    assert cursor.statements[-1][1][:3] == ("Ana Lima", "ana+festa@example.com", 28)
    assert connection.committed
    assert cursor.closed
    assert connection.closed


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


@pytest.mark.parametrize(
    "params,expected", [({}, (20, 0)), ({"limit": 100, "offset": 5}, (100, 5))]
)
def test_listagem_parametriza_paginacao(fake_database, params, expected):
    cursor, connection = fake_database
    response = client.get("/clientes", params=params)
    assert response.status_code == 200
    assert response.json() == []
    assert cursor.statements == [
        ("SELECT * FROM clientes ORDER BY id LIMIT %s OFFSET %s", expected)
    ]
    assert cursor.closed and connection.closed


@pytest.mark.parametrize("params", [
    {"limit": 0}, {"limit": -1}, {"limit": 101}, {"limit": "abc"},
    {"offset": -1}, {"offset": "abc"}, {"limit": "1.5"}, {"offset": "0.5"},
])
def test_paginacao_invalida_nao_acessa_banco(monkeypatch, params):
    def acesso_indevido():
        pytest.fail("Paginação inválida não deve abrir conexão")

    monkeypatch.setattr(app_module, "conectar_banco", acesso_indevido)
    assert client.get("/clientes", params=params).status_code == 422


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


REQUISICOES = [
    ("GET", "/clientes", None),
    ("GET", "/clientes/1", None),
    ("POST", "/clientes", {"nome": "Ana", "email": "ana@example.com", "idade": 28}),
    ("PUT", "/clientes/1", {"nome": "Ana", "email": "ana@example.com", "idade": 28}),
    ("DELETE", "/clientes/1", None),
]


def erro_operacional(*args, **kwargs):
    raise app_module.mysql.connector.OperationalError("SQL e senha que não devem ser expostos")


@pytest.mark.parametrize("metodo,rota,dados", REQUISICOES)
def test_conexao_indisponivel_retorna_503(monkeypatch, caplog, metodo, rota, dados):
    monkeypatch.setattr(app_module, "conectar_banco", erro_operacional)

    response = client.request(metodo, rota, json=dados)

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Banco de dados temporariamente indisponível. Tente novamente mais tarde."
    }
    assert "SQL e senha" not in caplog.text


@pytest.mark.parametrize("metodo,rota,dados", REQUISICOES)
def test_falha_na_criacao_do_cursor_fecha_conexao(
    fake_database, monkeypatch, metodo, rota, dados
):
    cursor, connection = fake_database
    monkeypatch.setattr(connection, "cursor", erro_operacional)

    response = client.request(metodo, rota, json=dados)

    assert response.status_code == 503
    assert connection.closed
    assert not cursor.closed


@pytest.mark.parametrize("metodo,rota,dados", REQUISICOES)
def test_falha_na_consulta_libera_recursos(fake_database, monkeypatch, metodo, rota, dados):
    cursor, connection = fake_database
    monkeypatch.setattr(cursor, "execute", erro_operacional)

    response = client.request(metodo, rota, json=dados)

    assert response.status_code == 503
    assert cursor.closed and connection.closed
    assert not connection.committed
    assert connection.rolled_back == (metodo in {"POST", "PUT", "DELETE"})


@pytest.mark.parametrize("metodo,rota,dados", REQUISICOES[2:])
def test_falha_no_commit_tenta_rollback(fake_database, monkeypatch, metodo, rota, dados):
    cursor, connection = fake_database
    cursor.one = {"id": 1}
    monkeypatch.setattr(connection, "commit", erro_operacional)

    response = client.request(metodo, rota, json=dados)

    assert response.status_code == 503
    assert connection.rolled_back
    assert cursor.closed and connection.closed


@pytest.mark.parametrize("metodo,rota,dados,leitura", [
    (*REQUISICOES[0], "fetchall"),
    (*REQUISICOES[1], "fetchone"),
    (*REQUISICOES[3], "fetchone"),
])
def test_falha_na_leitura_libera_recursos(
    fake_database, monkeypatch, metodo, rota, dados, leitura
):
    cursor, connection = fake_database
    monkeypatch.setattr(cursor, leitura, erro_operacional)

    response = client.request(metodo, rota, json=dados)

    assert response.status_code == 503
    assert cursor.closed and connection.closed


def test_falha_no_rollback_nao_oculta_erro_original(fake_database, monkeypatch):
    cursor, connection = fake_database
    monkeypatch.setattr(cursor, "execute", erro_operacional)
    monkeypatch.setattr(connection, "rollback", erro_operacional)

    response = client.post("/clientes", json=REQUISICOES[2][2])

    assert response.status_code == 503
    assert cursor.closed and connection.closed


@pytest.mark.parametrize("falha_operacao", [False, True])
@pytest.mark.parametrize("recurso", ["cursor", "connection"])
def test_falha_no_fechamento_preserva_resposta(
    fake_database, monkeypatch, falha_operacao, recurso
):
    cursor, connection = fake_database
    alvo = cursor if recurso == "cursor" else connection

    def fechar_com_erro():
        alvo.closed = True
        erro_operacional()

    monkeypatch.setattr(alvo, "close", fechar_com_erro)
    if falha_operacao:
        monkeypatch.setattr(cursor, "execute", erro_operacional)

    response = client.get("/clientes")

    assert response.status_code == (503 if falha_operacao else 200)
    assert cursor.closed and connection.closed


@pytest.mark.parametrize("erro", [
    app_module.mysql.connector.InterfaceError("Detalhe interno"),
    app_module.mysql.connector.ProgrammingError("SQL interno"),
])
def test_erros_mysql_tem_resposta_generica(fake_database, monkeypatch, erro):
    cursor, connection = fake_database

    def falhar(*args):
        raise erro

    monkeypatch.setattr(cursor, "execute", falhar)
    response = client.get("/clientes")

    indisponivel = isinstance(erro, app_module.mysql.connector.InterfaceError)
    assert response.status_code == (503 if indisponivel else 500)
    assert "interno" not in response.text
    assert cursor.closed and connection.closed
