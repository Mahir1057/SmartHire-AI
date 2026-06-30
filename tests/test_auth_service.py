import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user import UserRole
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService


def test_register_defaults_to_candidate(db_session: Session) -> None:
    service = AuthService(db_session)
    user = service.register(
        UserCreate(fullname="Grace Hopper", email="grace@example.com", password="StrongPass123")
    )

    assert user.id
    assert user.role == UserRole.candidate


def test_login_rejects_bad_password(db_session: Session) -> None:
    service = AuthService(db_session)
    service.register(UserCreate(fullname="Grace Hopper", email="grace@example.com", password="StrongPass123"))

    with pytest.raises(HTTPException) as exc:
        service.login("grace@example.com", "wrong-password")

    assert exc.value.status_code == 401

