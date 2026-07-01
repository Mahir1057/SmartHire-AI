from fastapi.testclient import TestClient


def _register_and_login(client: TestClient) -> dict:
    client.post(
        "/api/v1/auth/register",
        json={
            "fullname": "Answer Candidate",
            "email": "answers@example.com",
            "password": "StrongPass123",
            "role": "candidate",
        },
    )
    return client.post(
        "/api/v1/auth/login",
        data={"username": "answers@example.com", "password": "StrongPass123"},
    ).json()


def _create_interview(client: TestClient, token: str) -> dict:
    response = client.post(
        "/api/v1/interviews",
        headers={"Authorization": f"Bearer {token}"},
        json={"interview_type": "technical", "difficulty": "medium", "question_count": 2},
    )
    assert response.status_code == 201
    return response.json()["interview"]


def test_save_answer_requires_in_progress_interview(client: TestClient) -> None:
    tokens = _register_and_login(client)
    interview = _create_interview(client, tokens["access_token"])

    response = client.post(
        f"/api/v1/interviews/{interview['id']}/answers",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={"question_id": interview["questions"][0]["id"], "transcript": "My answer."},
    )

    assert response.status_code == 409


def test_candidate_can_save_answer_and_upload_media(client: TestClient) -> None:
    tokens = _register_and_login(client)
    interview = _create_interview(client, tokens["access_token"])
    client.post(
        f"/api/v1/interviews/{interview['id']}/start",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    saved = client.post(
        f"/api/v1/interviews/{interview['id']}/answers",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={"question_id": interview["questions"][0]["id"], "transcript": "I would validate constraints first."},
    )
    assert saved.status_code == 201
    answer = saved.json()
    assert answer["transcript"] == "I would validate constraints first."

    audio = client.post(
        f"/api/v1/interviews/{interview['id']}/answers/{answer['id']}/audio",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        files={"file": ("answer.wav", b"audio-bytes", "audio/wav")},
    )
    assert audio.status_code == 200
    assert audio.json()["audio_path"]

    video = client.post(
        f"/api/v1/interviews/{interview['id']}/answers/{answer['id']}/video",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        files={"file": ("answer.mp4", b"video-bytes", "video/mp4")},
    )
    assert video.status_code == 200
    assert video.json()["video_path"]

    listed = client.get(
        f"/api/v1/interviews/{interview['id']}/answers",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_answer_transcript_upserts_for_same_question(client: TestClient) -> None:
    tokens = _register_and_login(client)
    interview = _create_interview(client, tokens["access_token"])
    client.post(
        f"/api/v1/interviews/{interview['id']}/start",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    first = client.post(
        f"/api/v1/interviews/{interview['id']}/answers",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={"question_id": interview["questions"][0]["id"], "transcript": "First version."},
    ).json()
    second = client.post(
        f"/api/v1/interviews/{interview['id']}/answers",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={"question_id": interview["questions"][0]["id"], "transcript": "Updated version."},
    ).json()

    assert second["id"] == first["id"]
    assert second["transcript"] == "Updated version."
