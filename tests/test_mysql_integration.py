import os

import mysql.connector
import pytest
from fastapi.testclient import TestClient

import app as app_module

pytestmark = pytest.mark.skipif(
    os.getenv("MYSQL_INTEGRATION") != "1", reason="MySQL isolado não habilitado"
)


@pytest.fixture
def mysql_client(monkeypatch):
    # Host e banco fixos impedem que .env direcione o teste a um banco comercial.
    def connect():
        return mysql.connector.connect(
            host="127.0.0.1",
            port=3306,
            user="integration",
            password=os.environ["MYSQL_TEST_PASSWORD"],
            database="customer_api_test",
        )

    connection = connect()
    cursor = connection.cursor()
    try:
        cursor.execute("DROP TABLE IF EXISTS clientes")
        cursor.execute(
            "CREATE TABLE clientes (id INT AUTO_INCREMENT PRIMARY KEY, "
            "nome VARCHAR(100) NOT NULL, email VARCHAR(150) NOT NULL, idade INT NOT NULL)"
        )
        connection.commit()
        monkeypatch.setattr(app_module, "conectar_banco", connect)
        with TestClient(app_module.app) as client:
            yield client
    finally:
        try:
            cursor.execute("DROP TABLE IF EXISTS clientes")
            connection.commit()
        finally:
            cursor.close()
            connection.close()


def test_crud_persiste_no_mysql(mysql_client):
    client = mysql_client
    data = {"nome": "  Ana Lima  ", "email": "ANA@example.com", "idade": 28}
    created = client.post("/clientes", json=data)
    assert created.status_code == 201
    client_id = created.json()["id"]
    expected = {"id": client_id, "nome": "Ana Lima", "email": "ana@example.com", "idade": 28}
    fetched = client.get(f"/clientes/{client_id}")
    assert fetched.status_code == 200
    assert fetched.json() == expected
    assert client.get("/clientes").json() == [expected]

    updated = {"nome": "Ana Moretti", "email": "ana.moretti@example.com", "idade": 29}
    assert client.put(f"/clientes/{client_id}", json=updated).status_code == 200
    assert client.get(f"/clientes/{client_id}").json() == {"id": client_id, **updated}
    # Atualizar com valores iguais também deve funcionar com o rowcount padrão do MySQL.
    assert client.put(f"/clientes/{client_id}", json=updated).status_code == 200
    assert client.delete(f"/clientes/{client_id}").status_code == 200
    assert client.get(f"/clientes/{client_id}").status_code == 404
    assert client.delete(f"/clientes/{client_id}").status_code == 404
    assert client.put(f"/clientes/{client_id}", json=updated).status_code == 404
    assert client.get("/clientes").json() == []


def test_entrada_invalida_nao_persiste_no_mysql(mysql_client):
    response = mysql_client.post(
        "/clientes", json={"nome": " ", "email": "invalido", "idade": -1}
    )
    assert response.status_code == 422
    assert mysql_client.get("/clientes").json() == []
