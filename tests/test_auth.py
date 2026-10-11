import pytest
from fastapi.testclient import TestClient

import app as app_module

client = TestClient(app_module.app)
ROUTES = [
    ("GET", "/clientes"),
    ("GET", "/clientes/1"),
    ("POST", "/clientes"),
    ("PUT", "/clientes/1"),
    ("DELETE", "/clientes/1"),
]


@pytest.fixture(autouse=True)
def banco_proibido(monkeypatch):
    def connect():
        pytest.fail("Requisição não autorizada não deve acessar o banco")

    monkeypatch.setattr(app_module, "conectar_banco", connect)


@pytest.mark.parametrize("method,path", ROUTES)
@pytest.mark.parametrize("key", [None, "", "incorreta", "unit-test-onlÿ"])
def test_chave_invalida_retorna_401(monkeypatch, caplog, method, path, key):
    monkeypatch.setenv("API_KEY", "unit-test-only")
    headers = {} if key is None else {"X-API-Key": key.encode("utf-8")}
    response = client.request(method, path, headers=headers, json={
        "nome": "Ana", "email": "ana@example.com", "idade": 28,
    })
    assert response.status_code == 401
    assert response.json() == {"detail": "Chave de API ausente ou inválida."}
    assert response.headers["WWW-Authenticate"] == "APIKey"
    assert "unit-test-only" not in response.text + caplog.text


@pytest.mark.parametrize("method,path", ROUTES)
@pytest.mark.parametrize("configured", [None, "", "   "])
def test_sem_configuracao_bloqueia_acesso(monkeypatch, method, path, configured):
    if configured is None:
        monkeypatch.delenv("API_KEY", raising=False)
    else:
        monkeypatch.setenv("API_KEY", configured)
    response = client.request(method, path, headers={"X-API-Key": "qualquer"})
    assert response.status_code == 503
    assert response.json() == {"detail": "Autenticação não configurada."}


def test_raiz_e_documentacao_publicas_sem_chave(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    assert client.get("/").status_code == 200
    assert client.get("/docs").status_code == 200
    schema = client.get("/openapi.json").json()
    assert schema["components"]["securitySchemes"]["APIKeyHeader"] == {
        "type": "apiKey", "in": "header", "name": "X-API-Key",
    }
    for method, path in ROUTES:
        schema_path = path.replace("/1", "/{cliente_id}")
        assert schema["paths"][schema_path][method.lower()]["security"] == [
            {"APIKeyHeader": []}
        ]
    assert not schema["paths"]["/"]["get"].get("security")
