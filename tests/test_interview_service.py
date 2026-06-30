from sqlalchemy.orm import Session
import asyncio

from app.models.interview import InterviewDifficulty, InterviewStatus, InterviewType
from app.repositories.interview_repository import InterviewRepository
from app.repositories.resume_repository import ResumeRepository
from app.schemas.interview import InterviewCreate
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService
from app.services.interview_service import InterviewService


def test_create_interview_generates_questions(db_session: Session) -> None:
    user = AuthService(db_session).register(
        UserCreate(fullname="Ada Lovelace", email="ada@example.com", password="StrongPass123")
    )
    service = InterviewService(InterviewRepository(db_session), ResumeRepository(db_session))

    interview = asyncio.run(
        service.create_interview(
            user,
            InterviewCreate(
                interview_type=InterviewType.hr,
                difficulty=InterviewDifficulty.easy,
                question_count=3,
            ),
        )
    )

    assert interview.id
    assert interview.status == InterviewStatus.created
    assert len(interview.questions) == 3
    assert interview.questions[0].category == InterviewType.hr


def test_start_and_finish_interview(db_session: Session) -> None:
    user = AuthService(db_session).register(
        UserCreate(fullname="Grace Hopper", email="grace@example.com", password="StrongPass123")
    )
    service = InterviewService(InterviewRepository(db_session), ResumeRepository(db_session))

    interview = asyncio.run(
        service.create_interview(
            user,
            InterviewCreate(
                interview_type=InterviewType.technical,
                difficulty=InterviewDifficulty.medium,
                question_count=2,
            ),
        )
    )

    assert interview.status == InterviewStatus.created
    assert len(interview.questions) == 2

    started = service.start_interview(user, interview.id)
    assert started.status == InterviewStatus.in_progress
    assert started.started_at is not None

    finished = service.finish_interview(user, interview.id)
    assert finished.status == InterviewStatus.completed
    assert finished.completed_at is not None
