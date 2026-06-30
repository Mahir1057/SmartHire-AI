# SmartHire AI Backend

Production-oriented FastAPI backend scaffold for SmartHire AI.

This first increment implements **Module 1: Authentication** only:

- Register
- Login
- Refresh token
- Logout
- Forgot password
- Reset password
- JWT authentication dependency
- Role-based access dependency

Future platform modules are represented in the package layout but intentionally not implemented yet.

## Local Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
docker compose up -d postgres redis
alembic upgrade head
uvicorn app.main:app --reload
```

Swagger UI is available at `http://localhost:8000/docs`.

## Test

```powershell
pytest
```

## Example Auth Flow

Register:

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "fullname": "Ada Lovelace",
  "email": "ada@example.com",
  "password": "StrongPass123!",
  "role": "candidate"
}
```

Login:

```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=ada@example.com&password=StrongPass123!
```

Response:

```json
{
  "access_token": "eyJ...",
  "refresh_token": "Q8...",
  "token_type": "bearer"
}
```

