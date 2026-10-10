# Customer Management API

[![Quality](https://github.com/morettichaves/customer-management-api/actions/workflows/quality.yml/badge.svg)](https://github.com/morettichaves/customer-management-api/actions/workflows/quality.yml)

API REST para gerenciamento de clientes construída com **Python, FastAPI e MySQL**.

O projeto demonstra operações CRUD, integração com banco de dados, validação de entrada, tratamento de erros, testes automatizados e integração contínua.

## Contexto e decisões

Este é um projeto de estudo de Back-End: centralizar um cadastro de clientes e oferecer operações consistentes para criar, consultar, atualizar e excluir registros.

- **Solução:** API REST com FastAPI e persistência em MySQL.
- **Validação:** Pydantic limita tamanho dos campos e faixa de idade; o e-mail recebe uma verificação básica de formato e é convertido para minúsculas.
- **Acesso a dados:** consultas SQL parametrizadas, com fechamento de cursor e conexão no fluxo normal das rotas.
- **Comportamento HTTP:** criação retorna 201, registros inexistentes retornam 404 e entradas inválidas retornam 422.
- **Qualidade:** testes do contrato HTTP e integração contínua com lint e cobertura mínima exigida de 80%.

O repositório apresenta uma API de estudo, não um sistema já validado para uso com dados reais de clientes. Veja os limites atuais e a revisão técnica abaixo.

## Demonstração

A documentação interativa é gerada automaticamente pelo FastAPI com Swagger UI.

![Customer Management API - Swagger](screenshots/swagger-api.png)

## Funcionalidades

- Criar, listar, consultar, atualizar e excluir clientes
- Persistência de dados com MySQL
- Limites de nome e idade e verificação básica de e-mail com Pydantic
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

Você pode copiar o exemplo sem credenciais reais:

```powershell
Copy-Item .env.example .env
```

Depois ajuste os valores para o seu MySQL local:

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

Os testes atuais substituem o banco por `FakeConnection` e `FakeCursor`. Eles verificam respostas, comandos SQL e fechamento de recursos nos caminhos cobertos, sem criar clientes em um MySQL real. A cobertura alta não substitui um teste de integração com banco.

## Exemplo de uso

Com MySQL configurado, tabela criada e servidor iniciado, envie no Swagger (`/docs`) um `POST /clientes` com:

```json
{
  "nome": "Ana Lima",
  "email": "ana@example.com",
  "idade": 28
}
```

Uma criação bem-sucedida retorna HTTP 201 e o ID gerado pelo banco. Use esse ID em `GET /clientes/{cliente_id}`, `PUT /clientes/{cliente_id}` e `DELETE /clientes/{cliente_id}`. Execute esses exemplos em um banco de teste.

## Limites atuais e próximos passos

- Não há autenticação ou autorização; as operações de cadastro não devem ser expostas com dados reais sem controle de acesso.
- A listagem retorna todos os clientes, sem paginação.
- A rota `/` verifica apenas que a aplicação responde, não a disponibilidade do MySQL.
- A verificação de e-mail ainda aceita alguns formatos inválidos, e o nome não é normalizado antes da validação.
- Falhas de conexão ou SQL ainda não têm uma resposta padronizada de indisponibilidade; o fechamento da conexão também precisa cobrir falhas na criação do cursor.

Prioridade sugerida: reforçar validação de entrada, tratar falhas de banco e testar a integração MySQL; depois evoluir paginação e controle de acesso. O registro completo está em [docs/REVISAO-TECNICA.md](docs/REVISAO-TECNICA.md).

## Estrutura

```text
customer-management-api/
├── .github/workflows/quality.yml
├── screenshots/
├── docs/REVISAO-TECNICA.md
├── tests/
│   └── test_app.py
├── AGENTS.md
├── .env.example
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
