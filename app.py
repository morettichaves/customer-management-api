from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import mysql.connector
import os

load_dotenv()

app = FastAPI()


class Cliente(BaseModel):
    nome: str
    email: str
    idade: int


def conectar_banco():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )


@app.get("/")
def home():
    return {"message": "Customer Management API is running!"}


@app.get("/clientes")
def listar_clientes():
    conexao = conectar_banco()
    cursor = conexao.cursor(dictionary=True)

    cursor.execute("SELECT * FROM clientes")
    clientes = cursor.fetchall()

    cursor.close()
    conexao.close()

    return clientes


@app.get("/clientes/{cliente_id}")
def buscar_cliente(cliente_id: int):
    conexao = conectar_banco()
    cursor = conexao.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM clientes WHERE id = %s",
        (cliente_id,)
    )

    cliente = cursor.fetchone()

    cursor.close()
    conexao.close()

    if cliente is None:
        raise HTTPException(
            status_code=404,
            detail="Cliente não encontrado"
        )

    return cliente


@app.post("/clientes")
def cadastrar_cliente(cliente: Cliente):
    conexao = conectar_banco()
    cursor = conexao.cursor()

    sql = """
    INSERT INTO clientes (nome, email, idade)
    VALUES (%s, %s, %s)
    """

    valores = (
        cliente.nome,
        cliente.email,
        cliente.idade
    )

    cursor.execute(sql, valores)
    conexao.commit()

    novo_id = cursor.lastrowid

    cursor.close()
    conexao.close()

    return {
        "message": "Cliente cadastrado com sucesso!",
        "id": novo_id,
        "cliente": cliente
    }


@app.put("/clientes/{cliente_id}")
def atualizar_cliente(cliente_id: int, cliente: Cliente):
    conexao = conectar_banco()
    cursor = conexao.cursor(dictionary=True)

    # Primeiro verifica se o cliente existe
    cursor.execute(
        "SELECT * FROM clientes WHERE id = %s",
        (cliente_id,)
    )

    cliente_existente = cursor.fetchone()

    if cliente_existente is None:
        cursor.close()
        conexao.close()

        raise HTTPException(
            status_code=404,
            detail="Cliente não encontrado"
        )

    # Atualiza os dados
    sql = """
    UPDATE clientes
    SET nome = %s, email = %s, idade = %s
    WHERE id = %s
    """

    valores = (
        cliente.nome,
        cliente.email,
        cliente.idade,
        cliente_id
    )

    cursor.execute(sql, valores)
    conexao.commit()

    cursor.close()
    conexao.close()

    return {
        "message": "Cliente atualizado com sucesso!",
        "id": cliente_id
    }

@app.delete("/clientes/{cliente_id}")
def excluir_cliente(cliente_id: int):
    conexao = conectar_banco()
    cursor = conexao.cursor()

    cursor.execute(
        "DELETE FROM clientes WHERE id = %s",
        (cliente_id,)
    )

    conexao.commit()

    linhas_afetadas = cursor.rowcount

    cursor.close()
    conexao.close()

    if linhas_afetadas == 0:
        raise HTTPException(
            status_code=404,
            detail="Cliente não encontrado"
        )

    return {
        "message": "Cliente excluído com sucesso!"
    }