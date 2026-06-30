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

The second increment implements **Module 2: Resume Upload and Parsing**:

- Authenticated candidate resume upload
- PDF text extraction
- Skill extraction
- Summary generation
- Resume listing, search, detail, and deletion
- Local development file storage

The third increment implements **Module 3: AI Interview Generation and Interview Session Management**:

- Create interview sessions
- Generate interview questions from resume skills when available
- OpenAI-compatible generator with local deterministic fallback
- Start and finish interview sessions
- List, filter, and inspect interview sessions

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

When running inside Docker Compose, the API container automatically uses `postgres:5432` and `redis:6379` through `docker-compose.yml`. Keep `.env` on `localhost` if you run commands from your host machine.

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

Create interview:

```http
POST /api/v1/interviews
Authorization: Bearer ACCESS_TOKEN
Content-Type: application/json

{
  "interview_type": "technical",
  "difficulty": "medium",
  "resume_id": 1,
  "question_count": 5
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

Upload resume:

```http
POST /api/v1/resumes
Authorization: Bearer ACCESS_TOKEN
Content-Type: multipart/form-data

file=@resume.pdf
```

Response:

```json
{
  "message": "Resume uploaded and parsed successfully",
  "resume": {
    "id": 1,
    "user_id": 1,
    "filename": "resume.pdf",
    "content_type": "application/pdf",
    "extracted_text": "Built Python FastAPI services...",
    "extracted_skills": ["docker", "fastapi", "postgresql", "python"],
    "summary": "Built Python FastAPI services. Key skills detected: docker, fastapi, postgresql, python.",
    "upload_date": "2026-06-30T16:20:00Z"
  }
}
```
