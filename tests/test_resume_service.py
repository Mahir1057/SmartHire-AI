from pathlib import Path

from sqlalchemy.orm import Session

from app.models.resume import Resume
from app.models.user import UserRole
from app.repositories.resume_repository import ResumeRepository
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService
from app.services.resume_service import ResumeService


def test_extract_skills_detects_known_keywords(db_session: Session, tmp_path: Path) -> None:
    service = ResumeService(ResumeRepository(db_session), storage_root=tmp_path)

    skills = service.extract_skills("Built Python FastAPI services with PostgreSQL, Redis, Docker, and OpenAI.")

    assert skills == ["docker", "fastapi", "openai", "postgresql", "python", "redis"]


def test_list_my_resumes_returns_only_owner_records(db_session: Session, tmp_path: Path) -> None:
    auth = AuthService(db_session)
    owner = auth.register(UserCreate(fullname="Ada", email="ada@example.com", password="StrongPass123"))
    other = auth.register(UserCreate(fullname="Grace", email="grace@example.com", password="StrongPass123"))
    assert owner.role == UserRole.candidate

    repo = ResumeRepository(db_session)
    service = ResumeService(repo, storage_root=tmp_path)
    repo.create(
        Resume(
            user_id=owner.id,
            filename="owner.pdf",
            storage_path=str(tmp_path / "owner.pdf"),
            content_type="application/pdf",
            extracted_text="Python FastAPI",
            extracted_skills=["python", "fastapi"],
            summary="Python FastAPI.",
        )
    )
    repo.create(
        Resume(
            user_id=other.id,
            filename="other.pdf",
            storage_path=str(tmp_path / "other.pdf"),
            content_type="application/pdf",
            extracted_text="React",
            extracted_skills=["react"],
            summary="React.",
        )
    )

    result = service.list_my_resumes(owner)

    assert result.total == 1
    assert result.items[0].filename == "owner.pdf"
