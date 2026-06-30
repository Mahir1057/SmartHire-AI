from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.interview import InterviewDifficulty, InterviewStatus, InterviewType


class InterviewCreate(BaseModel):
    interview_type: InterviewType
    difficulty: InterviewDifficulty = InterviewDifficulty.medium
    resume_id: int | None = None
    question_count: int = Field(default=5, ge=1, le=20)


class InterviewQuestionRead(BaseModel):
    id: int
    question: str
    category: InterviewType
    difficulty: InterviewDifficulty
    expected_answer: str
    order_index: int

    model_config = ConfigDict(from_attributes=True)


class InterviewSessionRead(BaseModel):
    id: int
    user_id: int
    resume_id: int | None
    interview_type: InterviewType
    difficulty: InterviewDifficulty
    status: InterviewStatus
    question_count: int
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    questions: list[InterviewQuestionRead] = []

    model_config = ConfigDict(from_attributes=True)


class InterviewListItem(BaseModel):
    id: int
    resume_id: int | None
    interview_type: InterviewType
    difficulty: InterviewDifficulty
    status: InterviewStatus
    question_count: int
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InterviewListResponse(BaseModel):
    total: int
    items: list[InterviewListItem]


class InterviewSessionCreated(BaseModel):
    message: str = "Interview session created and questions generated successfully"
    interview: InterviewSessionRead
