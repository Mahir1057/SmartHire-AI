from datetime import UTC, datetime

from fastapi import HTTPException, status

from app.ai.interview_generator import InterviewQuestionGenerator
from app.models.interview import InterviewQuestion, InterviewSession, InterviewStatus
from app.models.user import User
from app.repositories.interview_repository import InterviewRepository
from app.repositories.resume_repository import ResumeRepository
from app.schemas.interview import InterviewCreate, InterviewListResponse


class InterviewService:
    def __init__(
        self,
        interviews: InterviewRepository,
        resumes: ResumeRepository,
        generator: InterviewQuestionGenerator | None = None,
    ) -> None:
        self.interviews = interviews
        self.resumes = resumes
        self.generator = generator or InterviewQuestionGenerator()

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
