from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.interview import CandidateAnswer, InterviewQuestion, InterviewSession, InterviewStatus, InterviewType


class InterviewRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_session(self, interview: InterviewSession) -> InterviewSession:
        self.db.add(interview)
        self.db.commit()
        self.db.refresh(interview)
        return interview

    def add_questions(self, questions: list[InterviewQuestion]) -> list[InterviewQuestion]:
        self.db.add_all(questions)
        self.db.commit()
        for question in questions:
            self.db.refresh(question)
        return questions

    def get_by_id(self, interview_id: int) -> InterviewSession | None:
        statement = (
            select(InterviewSession)
            .options(selectinload(InterviewSession.questions), selectinload(InterviewSession.answers))
            .where(InterviewSession.id == interview_id)
        )
        return self.db.scalar(statement)

    def get_question_by_id(self, question_id: int) -> InterviewQuestion | None:
        return self.db.get(InterviewQuestion, question_id)

    def get_answer_by_id(self, answer_id: int) -> CandidateAnswer | None:
        return self.db.get(CandidateAnswer, answer_id)

    def get_answer_for_question(self, interview_id: int, question_id: int) -> CandidateAnswer | None:
        statement = select(CandidateAnswer).where(
            CandidateAnswer.interview_id == interview_id,
            CandidateAnswer.question_id == question_id,
        )
        return self.db.scalar(statement)

    def list_answers(self, interview_id: int) -> list[CandidateAnswer]:
        statement = select(CandidateAnswer).where(CandidateAnswer.interview_id == interview_id).order_by(
            CandidateAnswer.created_at.asc()
        )
        return list(self.db.scalars(statement))

    def save_answer(self, answer: CandidateAnswer) -> CandidateAnswer:
        self.db.add(answer)
        self.db.commit()
        self.db.refresh(answer)
        return answer

    def list_for_user(
        self,
        user_id: int,
        *,
        skip: int = 0,
        limit: int = 20,
        status: InterviewStatus | None = None,
        interview_type: InterviewType | None = None,
    ) -> list[InterviewSession]:
        statement = select(InterviewSession).where(InterviewSession.user_id == user_id)
        if status:
            statement = statement.where(InterviewSession.status == status)
        if interview_type:
            statement = statement.where(InterviewSession.interview_type == interview_type)
        statement = statement.order_by(InterviewSession.created_at.desc()).offset(skip).limit(limit)
        return list(self.db.scalars(statement))

    def count_for_user(
        self,
        user_id: int,
        *,
        status: InterviewStatus | None = None,
        interview_type: InterviewType | None = None,
    ) -> int:
        statement = select(func.count()).select_from(InterviewSession).where(InterviewSession.user_id == user_id)
        if status:
            statement = statement.where(InterviewSession.status == status)
        if interview_type:
            statement = statement.where(InterviewSession.interview_type == interview_type)
        return int(self.db.scalar(statement) or 0)

    def save(self, interview: InterviewSession) -> InterviewSession:
        self.db.commit()
        self.db.refresh(interview)
        return interview
