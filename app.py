import logging
import os
import secrets
from contextlib import contextmanager
from typing import Annotated

import mysql.connector
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Security, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, EmailStr, Field, StringConstraints, field_validator

load_dotenv()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Customer Management API",
    description="API REST para gerenciamento de clientes.",
    version="1.1.0",
)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def autenticar_chave(chave: Annotated[str | None, Security(api_key_header)]):
    configurada = os.getenv("API_KEY")
    if not configurada or not configurada.strip():
        raise HTTPException(status_code=503, detail="Autenticação não configurada.")
    if not chave or not secrets.compare_digest(chave.encode(), configurada.encode()):
        raise HTTPException(
            status_code=401,
            detail="Chave de API ausente ou inválida.",
            headers={"WWW-Authenticate": "APIKey"},
        )


clientes_router = APIRouter(dependencies=[Depends(autenticar_chave)])


class Cliente(BaseModel):
    nome: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)]
    email: EmailStr = Field(max_length=150)
    idade: int = Field(ge=0, le=130)

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, valor: str) -> str:
        return valor.lower()


def conectar_banco():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )


def fechar_recurso(recurso, tipo):
    try:
        recurso.close()
    except mysql.connector.Error:
        logger.warning("database_cleanup_failed", extra={"resource_type": tipo})


@contextmanager
def cursor_banco(*, dictionary=False, escrita=False):
    conexao = None
    cursor = None
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor(dictionary=dictionary)
        yield conexao, cursor
    except mysql.connector.Error as erro:
        if escrita and conexao is not None:
            try:
                conexao.rollback()
            except mysql.connector.Error:
                logger.warning("database_rollback_failed")
        logger.error("database_operation_failed", extra={"error_type": type(erro).__name__})
        if isinstance(erro, (mysql.connector.OperationalError, mysql.connector.InterfaceError)):
            raise HTTPException(
                status_code=503,
                detail="Banco de dados temporariamente indisponível. Tente novamente mais tarde.",
            ) from erro
        raise HTTPException(
            status_code=500, detail="Não foi possível concluir a operação."
        ) from erro
    finally:
        try:
            if cursor is not None:
                fechar_recurso(cursor, "cursor")
        finally:
            if conexao is not None:
                fechar_recurso(conexao, "connection")


@app.get("/")
def home():
    return {"message": "Customer Management API is running!"}


@clientes_router.get("/clientes")
def listar_clientes(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    with cursor_banco(dictionary=True) as (_, cursor):
        cursor.execute("SELECT * FROM clientes ORDER BY id LIMIT %s OFFSET %s", (limit, offset))
        return cursor.fetchall()


@clientes_router.get("/clientes/{cliente_id}")
def buscar_cliente(cliente_id: int):
    with cursor_banco(dictionary=True) as (_, cursor):
        cursor.execute("SELECT * FROM clientes WHERE id = %s", (cliente_id,))
        cliente = cursor.fetchone()

    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    return cliente


@clientes_router.post("/clientes", status_code=status.HTTP_201_CREATED)
def cadastrar_cliente(cliente: Cliente):
    with cursor_banco(escrita=True) as (conexao, cursor):
        cursor.execute(
            "INSERT INTO clientes (nome, email, idade) VALUES (%s, %s, %s)",
            (cliente.nome, cliente.email, cliente.idade),
        )
        conexao.commit()
        novo_id = cursor.lastrowid

    return {
        "message": "Cliente cadastrado com sucesso!",
        "id": novo_id,
        "cliente": cliente,
    }


@clientes_router.put("/clientes/{cliente_id}")
def atualizar_cliente(cliente_id: int, cliente: Cliente):
    with cursor_banco(dictionary=True, escrita=True) as (conexao, cursor):
        cursor.execute("SELECT * FROM clientes WHERE id = %s", (cliente_id,))

        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")

        cursor.execute(
            "UPDATE clientes SET nome = %s, email = %s, idade = %s WHERE id = %s",
            (cliente.nome, cliente.email, cliente.idade, cliente_id),
        )
        conexao.commit()

    return {"message": "Cliente atualizado com sucesso!", "id": cliente_id}


@clientes_router.delete("/clientes/{cliente_id}")
def excluir_cliente(cliente_id: int):
    with cursor_banco(escrita=True) as (conexao, cursor):
        cursor.execute("DELETE FROM clientes WHERE id = %s", (cliente_id,))
        conexao.commit()
        linhas_afetadas = cursor.rowcount

    if linhas_afetadas == 0:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    return {"message": "Cliente excluído com sucesso!"}


app.include_router(clientes_router)
