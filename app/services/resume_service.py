import re
from pathlib import Path
from secrets import token_hex

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.models.resume import Resume
from app.models.user import User
from app.repositories.resume_repository import ResumeRepository
from app.schemas.resume import ResumeListResponse
from app.services.resume_parser import ResumeParser


class ResumeService:
    allowed_content_types = {"application/pdf"}
    max_upload_bytes = 5 * 1024 * 1024
    skill_catalog = {
        "python",
        "fastapi",
        "django",
        "flask",
        "sqlalchemy",
        "postgresql",
        "mysql",
        "redis",
        "celery",
        "docker",
        "kubernetes",
        "aws",
        "s3",
        "graphql",
        "rest",
        "microservices",
        "machine learning",
        "nlp",
        "openai",
        "pandas",
        "numpy",
        "react",
        "node.js",
        "typescript",
        "javascript",
    }

    def __init__(
        self,
        repository: ResumeRepository,
        parser: ResumeParser | None = None,
        storage_root: str | Path | None = None,
    ) -> None:
        self.repository = repository
        self.parser = parser or ResumeParser()
        self.storage_root = Path(storage_root or settings.local_storage_path)

    async def upload_resume(self, user: User, file: UploadFile) -> Resume:
        if file.content_type not in self.allowed_content_types:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF resumes are supported")

        content = await file.read()
        if not content:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resume file is empty")
        if len(content) > self.max_upload_bytes:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Resume file is too large")

        extracted_text = self.parser.parse_pdf(content)
        skills = self.extract_skills(extracted_text)
        summary = self.generate_summary(extracted_text, skills)
        storage_path = self._store_file(user.id, file.filename or "resume.pdf", content)

        resume = Resume(
            user_id=user.id,
            filename=file.filename or "resume.pdf",
            storage_path=str(storage_path),
            content_type=file.content_type,
            extracted_text=extracted_text,
            extracted_skills=skills,
            summary=summary,
        )
        return self.repository.create(resume)

    def list_my_resumes(self, user: User, *, skip: int = 0, limit: int = 20, search: str | None = None) -> ResumeListResponse:
        total = self.repository.count_for_user(user.id, search=search)
        items = self.repository.list_for_user(user.id, skip=skip, limit=limit, search=search)
        return ResumeListResponse(total=total, items=items)

    def get_owned_resume(self, user: User, resume_id: int) -> Resume:
        resume = self.repository.get_by_id(resume_id)
        if resume is None or resume.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
        return resume

    def delete_owned_resume(self, user: User, resume_id: int) -> None:
        resume = self.get_owned_resume(user, resume_id)
        path = Path(resume.storage_path)
        self.repository.delete(resume)
        if path.exists() and path.is_file():
            path.unlink()

    def extract_skills(self, text: str) -> list[str]:
        normalized = text.lower()
        tokens = set(re.findall(r"[a-z0-9+#]+", normalized))
        found = []
        for skill in sorted(self.skill_catalog):
            if " " not in skill and "." not in skill and skill in tokens:
                found.append(skill)
                continue

            pattern = r"(?<![a-z0-9+#.-])" + re.escape(skill) + r"(?![a-z0-9+#.-])"
            if re.search(pattern, normalized):
                found.append(skill)
        return found

    @staticmethod
    def generate_summary(text: str, skills: list[str]) -> str:
        compact = " ".join(text.split())
        first_sentence = compact.split(".")[0][:220].strip()
        if skills:
            return f"{first_sentence}. Key skills detected: {', '.join(skills[:8])}."
        return f"{first_sentence}." if first_sentence else "Resume parsed successfully."

    def _store_file(self, user_id: int, filename: str, content: bytes) -> Path:
        safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", filename)
        directory = self.storage_root / "resumes" / str(user_id)
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / f"{token_hex(12)}_{safe_name}"
        target.write_bytes(content)
        return target
