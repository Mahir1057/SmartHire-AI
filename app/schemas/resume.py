from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ResumeRead(BaseModel):
    id: int
    user_id: int
    filename: str
    content_type: str
    extracted_text: str
    extracted_skills: list[str]
    summary: str
    upload_date: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeListItem(BaseModel):
    id: int
    filename: str
    extracted_skills: list[str]
    summary: str
    upload_date: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeListResponse(BaseModel):
    total: int
    items: list[ResumeListItem]


class ResumeUploadResponse(BaseModel):
    resume: ResumeRead
    message: str = Field(default="Resume uploaded and parsed successfully")
