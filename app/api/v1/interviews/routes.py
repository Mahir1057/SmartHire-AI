from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models.interview import InterviewStatus, InterviewType
from app.models.user import User, UserRole
from app.repositories.interview_repository import InterviewRepository
from app.repositories.resume_repository import ResumeRepository
from app.schemas.interview import (
    CandidateAnswerCreate,
    CandidateAnswerRead,
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


@router.post("/{interview_id}/answers", response_model=CandidateAnswerRead, status_code=status.HTTP_201_CREATED)
def save_answer(
    interview_id: int,
    payload: CandidateAnswerCreate,
    current_user: User = Depends(require_roles(UserRole.candidate)),
    service: InterviewService = Depends(get_interview_service),
):
    return service.save_answer(current_user, interview_id, payload)


@router.get("/{interview_id}/answers", response_model=list[CandidateAnswerRead])
def list_answers(
    interview_id: int,
    current_user: User = Depends(get_current_user),
    service: InterviewService = Depends(get_interview_service),
):
    return service.list_answers(current_user, interview_id)


@router.post("/{interview_id}/answers/{answer_id}/audio", response_model=CandidateAnswerRead)
async def upload_answer_audio(
    interview_id: int,
    answer_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles(UserRole.candidate)),
    service: InterviewService = Depends(get_interview_service),
):
    return await service.upload_answer_audio(current_user, interview_id, answer_id, file)


@router.post("/{interview_id}/answers/{answer_id}/video", response_model=CandidateAnswerRead)
async def upload_answer_video(
    interview_id: int,
    answer_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles(UserRole.candidate)),
    service: InterviewService = Depends(get_interview_service),
):
    return await service.upload_answer_video(current_user, interview_id, answer_id, file)
