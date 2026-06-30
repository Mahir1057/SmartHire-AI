from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models.user import User, UserRole
from app.repositories.resume_repository import ResumeRepository
from app.schemas.resume import ResumeListResponse, ResumeRead, ResumeUploadResponse
from app.services.resume_service import ResumeService

router = APIRouter()


def get_resume_service(db: Session = Depends(get_db)) -> ResumeService:
    return ResumeService(ResumeRepository(db))


@router.post("", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles(UserRole.candidate)),
    service: ResumeService = Depends(get_resume_service),
) -> ResumeUploadResponse:
    resume = await service.upload_resume(current_user, file)
    return ResumeUploadResponse(resume=resume)


@router.get("", response_model=ResumeListResponse)
def list_my_resumes(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, min_length=1, max_length=100),
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
) -> ResumeListResponse:
    return service.list_my_resumes(current_user, skip=skip, limit=limit, search=search)


@router.get("/{resume_id}", response_model=ResumeRead)
def get_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
):
    return service.get_owned_resume(current_user, resume_id)


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(
    resume_id: int,
    current_user: User = Depends(require_roles(UserRole.candidate)),
    service: ResumeService = Depends(get_resume_service),
) -> Response:
    service.delete_owned_resume(current_user, resume_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
