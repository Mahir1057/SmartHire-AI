from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models.interview import InterviewStatus, InterviewType
from app.models.user import User, UserRole
from app.repositories.interview_repository import InterviewRepository
from app.repositories.resume_repository import ResumeRepository
from app.schemas.interview import (
    InterviewCreate,
    InterviewListResponse,
    InterviewQuestionRead,
    InterviewSessionCreated,
    InterviewSessionRead,
)
from app.services.interview_service import InterviewService

router = APIRouter()


def get_interview_service(db: Session = Depends(get_db)) -> InterviewService:
    return InterviewService(InterviewRepository(db), ResumeRepository(db))


@router.post("", response_model=InterviewSessionCreated, status_code=status.HTTP_201_CREATED)
async def create_interview(
    payload: InterviewCreate,
    current_user: User = Depends(require_roles(UserRole.candidate)),
    service: InterviewService = Depends(get_interview_service),
) -> InterviewSessionCreated:
    interview = await service.create_interview(current_user, payload)
    return InterviewSessionCreated(interview=interview)


@router.get("", response_model=InterviewListResponse)
def list_interviews(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    status_filter: InterviewStatus | None = Query(default=None, alias="status"),
    interview_type: InterviewType | None = None,
    current_user: User = Depends(get_current_user),
    service: InterviewService = Depends(get_interview_service),
) -> InterviewListResponse:
    return service.list_my_interviews(
        current_user,
        skip=skip,
        limit=limit,
        status_filter=status_filter,
        interview_type=interview_type,
    )


@router.get("/{interview_id}", response_model=InterviewSessionRead)
def get_interview(
    interview_id: int,
    current_user: User = Depends(get_current_user),
    service: InterviewService = Depends(get_interview_service),
):
    return service.get_owned_interview(current_user, interview_id)


@router.get("/{interview_id}/questions", response_model=list[InterviewQuestionRead])
def get_interview_questions(
    interview_id: int,
    current_user: User = Depends(get_current_user),
    service: InterviewService = Depends(get_interview_service),
):
    return service.get_owned_interview(current_user, interview_id).questions


@router.post("/{interview_id}/start", response_model=InterviewSessionRead)
def start_interview(
    interview_id: int,
    current_user: User = Depends(require_roles(UserRole.candidate)),
    service: InterviewService = Depends(get_interview_service),
):
    return service.start_interview(current_user, interview_id)


@router.post("/{interview_id}/finish", response_model=InterviewSessionRead)
def finish_interview(
    interview_id: int,
    current_user: User = Depends(require_roles(UserRole.candidate)),
    service: InterviewService = Depends(get_interview_service),
):
    return service.finish_interview(current_user, interview_id)
