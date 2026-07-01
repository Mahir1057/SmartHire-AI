from datetime import UTC, datetime

import re
from pathlib import Path
from secrets import token_hex

from fastapi import HTTPException, UploadFile, status

from app.ai.interview_generator import InterviewQuestionGenerator
from app.core.config import settings
from app.models.interview import CandidateAnswer, InterviewQuestion, InterviewSession, InterviewStatus
from app.models.user import User
from app.repositories.interview_repository import InterviewRepository
from app.repositories.resume_repository import ResumeRepository
from app.schemas.interview import CandidateAnswerCreate, InterviewCreate, InterviewListResponse


class InterviewService:
    def __init__(
        self,
        interviews: InterviewRepository,
        resumes: ResumeRepository,
        generator: InterviewQuestionGenerator | None = None,
        storage_root: str | Path | None = None,
    ) -> None:
        self.interviews = interviews
        self.resumes = resumes
        self.generator = generator or InterviewQuestionGenerator()
        self.storage_root = Path(storage_root or settings.local_storage_path)

    async def create_interview(self, user: User, payload: InterviewCreate) -> InterviewSession:
        resume = None
        if payload.resume_id is not None:
            resume = self.resumes.get_by_id(payload.resume_id)
            if resume is None or resume.user_id != user.id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

        interview = self.interviews.create_session(
            InterviewSession(
                user_id=user.id,
                resume_id=resume.id if resume else None,
                interview_type=payload.interview_type,
                difficulty=payload.difficulty,
                question_count=payload.question_count,
            )
        )

        generated_questions = await self.generator.generate_questions(
            interview_type=payload.interview_type,
            difficulty=payload.difficulty,
            skills=resume.extracted_skills if resume else [],
            resume_summary=resume.summary if resume else None,
            count=payload.question_count,
        )
        questions = [
            InterviewQuestion(
                interview_id=interview.id,
                question=item["question"],
                expected_answer=item["expected_answer"],
                category=payload.interview_type,
                difficulty=payload.difficulty,
                order_index=index,
            )
            for index, item in enumerate(generated_questions, start=1)
        ]
        self.interviews.add_questions(questions)
        refreshed = self.interviews.get_by_id(interview.id)
        if refreshed is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Interview creation failed")
        return refreshed

    def list_my_interviews(
        self,
        user: User,
        *,
        skip: int = 0,
        limit: int = 20,
        status_filter: InterviewStatus | None = None,
        interview_type=None,
    ) -> InterviewListResponse:
        total = self.interviews.count_for_user(user.id, status=status_filter, interview_type=interview_type)
        items = self.interviews.list_for_user(
            user.id,
            skip=skip,
            limit=limit,
            status=status_filter,
            interview_type=interview_type,
        )
        return InterviewListResponse(total=total, items=items)

    def get_owned_interview(self, user: User, interview_id: int) -> InterviewSession:
        interview = self.interviews.get_by_id(interview_id)
        if interview is None or interview.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found")
        return interview

    def start_interview(self, user: User, interview_id: int) -> InterviewSession:
        interview = self.get_owned_interview(user, interview_id)
        if interview.status == InterviewStatus.completed:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Completed interviews cannot be restarted")
        if interview.status == InterviewStatus.created:
            interview.status = InterviewStatus.in_progress
            interview.started_at = datetime.now(UTC)
        return self.interviews.save(interview)

    def finish_interview(self, user: User, interview_id: int) -> InterviewSession:
        interview = self.get_owned_interview(user, interview_id)
        if interview.status == InterviewStatus.completed:
            return interview
        if interview.status == InterviewStatus.created:
            interview.started_at = datetime.now(UTC)
        interview.status = InterviewStatus.completed
        interview.completed_at = datetime.now(UTC)
        return self.interviews.save(interview)

    def save_answer(self, user: User, interview_id: int, payload: CandidateAnswerCreate) -> CandidateAnswer:
        interview = self._get_active_owned_interview(user, interview_id)
        question = self.interviews.get_question_by_id(payload.question_id)
        if question is None or question.interview_id != interview.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview question not found")

        answer = self.interviews.get_answer_for_question(interview.id, question.id)
        if answer is None:
            answer = CandidateAnswer(
                interview_id=interview.id,
                question_id=question.id,
                transcript=payload.transcript,
            )
        else:
            answer.transcript = payload.transcript
        return self.interviews.save_answer(answer)

    def list_answers(self, user: User, interview_id: int) -> list[CandidateAnswer]:
        interview = self.get_owned_interview(user, interview_id)
        return self.interviews.list_answers(interview.id)

    async def upload_answer_audio(self, user: User, interview_id: int, answer_id: int, file: UploadFile) -> CandidateAnswer:
        return await self._upload_answer_media(
            user,
            interview_id,
            answer_id,
            file,
            media_type="audio",
            allowed_prefix="audio/",
            max_bytes=25 * 1024 * 1024,
        )

    async def upload_answer_video(self, user: User, interview_id: int, answer_id: int, file: UploadFile) -> CandidateAnswer:
        return await self._upload_answer_media(
            user,
            interview_id,
            answer_id,
            file,
            media_type="video",
            allowed_prefix="video/",
            max_bytes=100 * 1024 * 1024,
        )

    def _get_active_owned_interview(self, user: User, interview_id: int) -> InterviewSession:
        interview = self.get_owned_interview(user, interview_id)
        if interview.status != InterviewStatus.in_progress:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Interview must be in progress before saving answers",
            )
        return interview

    async def _upload_answer_media(
        self,
        user: User,
        interview_id: int,
        answer_id: int,
        file: UploadFile,
        *,
        media_type: str,
        allowed_prefix: str,
        max_bytes: int,
    ) -> CandidateAnswer:
        interview = self._get_active_owned_interview(user, interview_id)
        answer = self.interviews.get_answer_by_id(answer_id)
        if answer is None or answer.interview_id != interview.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate answer not found")
        if not file.content_type or not file.content_type.startswith(allowed_prefix):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Only {media_type} uploads are supported")

        content = await file.read()
        if not content:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded media file is empty")
        if len(content) > max_bytes:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"{media_type.title()} file is too large")

        path = self._store_media_file(user.id, interview.id, media_type, file.filename or f"answer.{media_type}", content)
        if media_type == "audio":
            answer.audio_path = str(path)
        else:
            answer.video_path = str(path)
        return self.interviews.save_answer(answer)

    def _store_media_file(self, user_id: int, interview_id: int, media_type: str, filename: str, content: bytes) -> Path:
        safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", filename)
        directory = self.storage_root / "interviews" / str(user_id) / str(interview_id) / media_type
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / f"{token_hex(12)}_{safe_name}"
        target.write_bytes(content)
        return target
