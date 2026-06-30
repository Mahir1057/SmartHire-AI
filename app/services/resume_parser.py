from io import BytesIO

from fastapi import HTTPException, status
from pypdf import PdfReader


class ResumeParser:
    def parse_pdf(self, content: bytes) -> str:
        try:
            reader = PdfReader(BytesIO(content))
            page_text = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(page_text).strip()
        except Exception:
            text = self._fallback_decode(content)

        if not text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not extract text from resume PDF",
            )
        return text

    @staticmethod
    def _fallback_decode(content: bytes) -> str:
        return content.decode("utf-8", errors="ignore").strip()
