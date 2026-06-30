from fastapi import APIRouter

from app.api.v1.auth.routes import router as auth_router
from app.api.v1.interviews.routes import router as interviews_router
from app.api.v1.resumes.routes import router as resumes_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(resumes_router, prefix="/resumes", tags=["resumes"])
api_router.include_router(interviews_router, prefix="/interviews", tags=["interviews"])
