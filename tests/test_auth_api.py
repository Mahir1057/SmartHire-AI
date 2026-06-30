from fastapi.testclient import TestClient


def _register(client: TestClient, email: str = "ada@example.com") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "fullname": "Ada Lovelace",
            "email": email,
            "password": "StrongPass123",
            "role": "candidate",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_register_and_login(client: TestClient) -> None:
    user = _register(client)
    assert user["email"] == "ada@example.com"
    assert user["role"] == "candidate"

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "ada@example.com", "password": "StrongPass123"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["refresh_token"]


def test_duplicate_email_is_rejected(client: TestClient) -> None:
    _register(client)
    response = client.post(
        "/api/v1/auth/register",
        json={
            "fullname": "Ada Lovelace",
            "email": "ada@example.com",
            "password": "StrongPass123",
            "role": "candidate",
        },
    )

    assert response.status_code == 409


def test_me_requires_valid_access_token(client: TestClient) -> None:
    _register(client)
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "ada@example.com", "password": "StrongPass123"},
    ).json()

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {login['access_token']}"})

    assert response.status_code == 200
    assert response.json()["email"] == "ada@example.com"


def test_refresh_rotates_refresh_token(client: TestClient) -> None:
    _register(client)
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "ada@example.com", "password": "StrongPass123"},
    ).json()

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]})

    assert response.status_code == 200
    assert response.json()["refresh_token"] != login["refresh_token"]

    reused = client.post("/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]})
    assert reused.status_code == 401


def test_logout_revokes_refresh_token(client: TestClient) -> None:
    _register(client)
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "ada@example.com", "password": "StrongPass123"},
    ).json()

    response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": login["refresh_token"]},
        headers={"Authorization": f"Bearer {login['access_token']}"},
    )

    assert response.status_code == 204
    refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]})
    assert refresh.status_code == 401


def test_forgot_and_reset_password(client: TestClient) -> None:
    _register(client)
    forgot = client.post("/api/v1/auth/forgot-password", json={"email": "ada@example.com"})

    assert forgot.status_code == 200
    reset_token = forgot.json()["reset_token"]
    assert reset_token

    reset = client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": "NewStrongPass123"},
    )
    assert reset.status_code == 204

    login = client.post(
        "/api/v1/auth/login",
        data={"username": "ada@example.com", "password": "NewStrongPass123"},
    )
    assert login.status_code == 200

