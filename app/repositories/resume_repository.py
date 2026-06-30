from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.resume import Resume


class ResumeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, resume: Resume) -> Resume:
        self.db.add(resume)
        self.db.commit()
        self.db.refresh(resume)
        return resume

    def get_by_id(self, resume_id: int) -> Resume | None:
        return self.db.get(Resume, resume_id)

    def list_for_user(self, user_id: int, *, skip: int = 0, limit: int = 20, search: str | None = None) -> list[Resume]:
        statement = select(Resume).where(Resume.user_id == user_id)
        if search:
            statement = statement.where(Resume.filename.ilike(f"%{search}%"))
        statement = statement.order_by(Resume.upload_date.desc()).offset(skip).limit(limit)
        return list(self.db.scalars(statement))

    def count_for_user(self, user_id: int, *, search: str | None = None) -> int:
        statement = select(func.count()).select_from(Resume).where(Resume.user_id == user_id)
        if search:
            statement = statement.where(Resume.filename.ilike(f"%{search}%"))
        return int(self.db.scalar(statement) or 0)

    def delete(self, resume: Resume) -> None:
        self.db.delete(resume)
        self.db.commit()
