from fastapi.testclient import TestClient


def _register_and_login(client: TestClient, role: str = "candidate") -> dict:
    client.post(
        "/api/v1/auth/register",
        json={
            "fullname": "Ada Lovelace",
            "email": f"interview-{role}@example.com",
            "password": "StrongPass123",
            "role": role,
        },
    )
    return client.post(
        "/api/v1/auth/login",
        data={"username": f"interview-{role}@example.com", "password": "StrongPass123"},
    ).json()


def test_candidate_can_create_start_and_finish_interview(client: TestClient) -> None:
    tokens = _register_and_login(client)

    created = client.post(
        "/api/v1/interviews",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={"interview_type": "technical", "difficulty": "medium", "question_count": 3},
    )

    assert created.status_code == 201
    interview = created.json()["interview"]
    assert interview["status"] == "created"
    assert len(interview["questions"]) == 3

    started = client.post(
        f"/api/v1/interviews/{interview['id']}/start",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert started.status_code == 200
    assert started.json()["status"] == "in_progress"

    finished = client.post(
        f"/api/v1/interviews/{interview['id']}/finish",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert finished.status_code == 200
    assert finished.json()["status"] == "completed"


def test_recruiter_cannot_create_interview(client: TestClient) -> None:
    tokens = _register_and_login(client, role="recruiter")
    response = client.post(
        "/api/v1/interviews",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={"interview_type": "hr", "difficulty": "easy", "question_count": 2},
    )

    assert response.status_code == 403


def test_list_interviews_supports_status_filter(client: TestClient) -> None:
    tokens = _register_and_login(client)
    client.post(
        "/api/v1/interviews",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={"interview_type": "behavioral", "difficulty": "hard", "question_count": 1},
    )

    response = client.get(
        "/api/v1/interviews?status=created",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
