# Customer Management API

A REST API for customer management built with Python, FastAPI, and MySQL.

## Features

- Create customers
- List all customers
- Find a customer by ID
- Update customer information
- Delete customers
- MySQL database integration
- Interactive API documentation with Swagger

## Technologies

- Python
- FastAPI
- MySQL
- Pydantic
- Uvicorn
- python-dotenv

## API Endpoints

- `GET /`
- `GET /clientes`
- `GET /clientes/{cliente_id}`
- `POST /clientes`
- `PUT /clientes/{cliente_id}`
- `DELETE /clientes/{cliente_id}`

## Installation

Clone the repository:

```bash
git clone YOUR_REPOSITORY_URL
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the virtual environment on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file with your MySQL configuration:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=customer_management
```

Create the MySQL database:

```sql
CREATE DATABASE customer_management;
```

Create the customers table:

```sql
USE customer_management;

CREATE TABLE clientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    idade INT NOT NULL
);
```

Run the API:

```bash
uvicorn app:app --reload
```

Open the interactive API documentation in your browser:

`http://127.0.0.1:8000/docs`

## Author

Otavio Moretti

Junior Back-End Developer