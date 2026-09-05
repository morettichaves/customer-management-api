import os

import mysql.connector
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, field_validator

load_dotenv()

app = FastAPI(
    title="Customer Management API",
    description="API REST para gerenciamento de clientes.",
    version="1.1.0",
)


class Cliente(BaseModel):
    nome: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=150)
    idade: int = Field(ge=0, le=130)

    @field_validator("email")
    @classmethod
    def validar_email(cls, valor: str) -> str:
        email = valor.strip().lower()
        dominio = email.rsplit("@", maxsplit=1)[-1]

        if "@" not in email or "." not in dominio:
            raise ValueError("Informe um e-mail válido")

        return email


def conectar_banco():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )


@app.get("/")
def home():
    return {"message": "Customer Management API is running!"}


@app.get("/clientes")
def listar_clientes():
    conexao = conectar_banco()
    cursor = conexao.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM clientes")
        return cursor.fetchall()
    finally:
        cursor.close()
        conexao.close()


@app.get("/clientes/{cliente_id}")
def buscar_cliente(cliente_id: int):
    conexao = conectar_banco()
    cursor = conexao.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM clientes WHERE id = %s", (cliente_id,))
        cliente = cursor.fetchone()
    finally:
        cursor.close()
        conexao.close()

    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    return cliente


@app.post("/clientes", status_code=status.HTTP_201_CREATED)
def cadastrar_cliente(cliente: Cliente):
    conexao = conectar_banco()
    cursor = conexao.cursor()

    try:
        cursor.execute(
            "INSERT INTO clientes (nome, email, idade) VALUES (%s, %s, %s)",
            (cliente.nome, cliente.email, cliente.idade),
        )
        conexao.commit()
        novo_id = cursor.lastrowid
    finally:
        cursor.close()
        conexao.close()

    return {
        "message": "Cliente cadastrado com sucesso!",
        "id": novo_id,
        "cliente": cliente,
    }


@app.put("/clientes/{cliente_id}")
def atualizar_cliente(cliente_id: int, cliente: Cliente):
    conexao = conectar_banco()
    cursor = conexao.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM clientes WHERE id = %s", (cliente_id,))

        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")

        cursor.execute(
            "UPDATE clientes SET nome = %s, email = %s, idade = %s WHERE id = %s",
            (cliente.nome, cliente.email, cliente.idade, cliente_id),
        )
        conexao.commit()
    finally:
        cursor.close()
        conexao.close()

    return {"message": "Cliente atualizado com sucesso!", "id": cliente_id}


@app.delete("/clientes/{cliente_id}")
def excluir_cliente(cliente_id: int):
    conexao = conectar_banco()
    cursor = conexao.cursor()

    try:
        cursor.execute("DELETE FROM clientes WHERE id = %s", (cliente_id,))
        conexao.commit()
        linhas_afetadas = cursor.rowcount
    finally:
        cursor.close()
        conexao.close()

    if linhas_afetadas == 0:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    return {"message": "Cliente excluído com sucesso!"}
