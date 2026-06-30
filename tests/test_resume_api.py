from fastapi.testclient import TestClient


def _register_and_login(client: TestClient, role: str = "candidate") -> dict:
    client.post(
        "/api/v1/auth/register",
        json={
            "fullname": "Ada Lovelace",
            "email": f"{role}@example.com",
            "password": "StrongPass123",
            "role": role,
        },
    )
    return client.post(
        "/api/v1/auth/login",
        data={"username": f"{role}@example.com", "password": "StrongPass123"},
    ).json()


def test_candidate_can_upload_and_read_resume(client: TestClient) -> None:
    tokens = _register_and_login(client)
    response = client.post(
        "/api/v1/resumes",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        files={"file": ("resume.pdf", b"Python FastAPI PostgreSQL Redis Docker OpenAI", "application/pdf")},
    )

    assert response.status_code == 201
    payload = response.json()["resume"]
    assert payload["filename"] == "resume.pdf"
    assert payload["extracted_skills"] == ["docker", "fastapi", "openai", "postgresql", "python", "redis"]

    detail = client.get(
        f"/api/v1/resumes/{payload['id']}",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert detail.status_code == 200
    assert detail.json()["id"] == payload["id"]


def test_resume_upload_rejects_non_pdf(client: TestClient) -> None:
    tokens = _register_and_login(client)
    response = client.post(
        "/api/v1/resumes",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        files={"file": ("resume.txt", b"Python", "text/plain")},
    )

    assert response.status_code == 400


def test_recruiter_cannot_upload_resume(client: TestClient) -> None:
    tokens = _register_and_login(client, role="recruiter")
    response = client.post(
        "/api/v1/resumes",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        files={"file": ("resume.pdf", b"Python", "application/pdf")},
    )

    assert response.status_code == 403


def test_list_resumes_supports_search(client: TestClient) -> None:
    tokens = _register_and_login(client)
    client.post(
        "/api/v1/resumes",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        files={"file": ("backend-resume.pdf", b"Python FastAPI", "application/pdf")},
    )

    response = client.get(
        "/api/v1/resumes?search=backend",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
