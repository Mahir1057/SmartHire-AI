import asyncio
from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.interview import InterviewDifficulty, InterviewType
from app.repositories.interview_repository import InterviewRepository
from app.repositories.resume_repository import ResumeRepository
from app.schemas.interview import CandidateAnswerCreate, InterviewCreate
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService
from app.services.interview_service import InterviewService


def test_save_answer_requires_active_session(db_session: Session, tmp_path: Path) -> None:
    user = AuthService(db_session).register(
        UserCreate(fullname="Ada Lovelace", email="module4@example.com", password="StrongPass123")
    )
    service = InterviewService(InterviewRepository(db_session), ResumeRepository(db_session), storage_root=tmp_path)
    interview = asyncio.run(
        service.create_interview(
            user,
            InterviewCreate(
                interview_type=InterviewType.technical,
                difficulty=InterviewDifficulty.medium,
                question_count=1,
            ),
        )
    )

    with pytest.raises(HTTPException) as exc:
        service.save_answer(
            user,
            interview.id,
            CandidateAnswerCreate(question_id=interview.questions[0].id, transcript="Not yet."),
        )

    assert exc.value.status_code == 409


def test_save_answer_for_question(db_session: Session, tmp_path: Path) -> None:
    user = AuthService(db_session).register(
        UserCreate(fullname="Grace Hopper", email="module4-grace@example.com", password="StrongPass123")
    )
    service = InterviewService(InterviewRepository(db_session), ResumeRepository(db_session), storage_root=tmp_path)
    interview = asyncio.run(
        service.create_interview(
            user,
            InterviewCreate(
                interview_type=InterviewType.behavioral,
                difficulty=InterviewDifficulty.easy,
                question_count=1,
            ),
        )
    )
    service.start_interview(user, interview.id)

    answer = service.save_answer(
        user,
        interview.id,
        CandidateAnswerCreate(question_id=interview.questions[0].id, transcript="A structured answer."),
    )

    assert answer.id
    assert answer.transcript == "A structured answer."
