# Customer Management API

[![Quality](https://github.com/morettichaves/customer-management-api/actions/workflows/quality.yml/badge.svg)](https://github.com/morettichaves/customer-management-api/actions/workflows/quality.yml)

API REST para gerenciamento de clientes construída com **Python, FastAPI e MySQL**.

O projeto demonstra operações CRUD, integração com banco de dados, validação de entrada, tratamento de erros, testes automatizados e integração contínua.

## Demonstração

A documentação interativa é gerada automaticamente pelo FastAPI com Swagger UI.

![Customer Management API - Swagger](screenshots/swagger-api.png)

## Funcionalidades

- Criar, listar, consultar, atualizar e excluir clientes
- Persistência de dados com MySQL
- Validação de nome, e-mail e idade com Pydantic
- Credenciais protegidas por variáveis de ambiente
- Consultas SQL parametrizadas
- Respostas HTTP 404 e 422 para erros conhecidos
- Testes automatizados com cobertura mínima de 80%
- Lint e testes executados no GitHub Actions

## Tecnologias

- Python 3.12
- FastAPI
- MySQL Connector/Python
- Pydantic
- Pytest e pytest-cov
- Ruff
- GitHub Actions

## Endpoints

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/` | Verifica o estado da API |
| GET | `/clientes` | Lista todos os clientes |
| GET | `/clientes/{cliente_id}` | Busca um cliente |
| POST | `/clientes` | Cria um cliente |
| PUT | `/clientes/{cliente_id}` | Atualiza um cliente |
| DELETE | `/clientes/{cliente_id}` | Exclui um cliente |

## Instalação

```bash
git clone https://github.com/morettichaves/customer-management-api.git
cd customer-management-api
python -m venv .venv
```

No Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Banco de dados

```sql
CREATE DATABASE customer_management;
USE customer_management;

CREATE TABLE clientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    idade INT NOT NULL
);
```

Crie um arquivo `.env` na raiz:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=sua_senha
DB_NAME=customer_management
```

O arquivo `.env` está protegido pelo `.gitignore` e não deve ser enviado ao GitHub.

## Executando a API

```bash
uvicorn app:app --reload
```

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`

## Qualidade e testes

Instale as dependências de desenvolvimento:

```bash
pip install -r requirements-dev.txt
```

Execute:

```bash
ruff check .
pytest
```

Cada Pull Request executa automaticamente lint, testes e geração do relatório de cobertura.

## Estrutura

```text
customer-management-api/
├── .github/workflows/quality.yml
├── screenshots/
├── tests/
│   └── test_app.py
├── AGENTS.md
├── app.py
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

## Autor

**Otávio Moretti** — Desenvolvedor Back-End Júnior

- [GitHub](https://github.com/morettichaves)
- [LinkedIn](https://www.linkedin.com/in/otavio-moretti)
