import json

import httpx

from app.core.config import settings
from app.models.interview import InterviewDifficulty, InterviewType


class GeneratedQuestion(dict):
    question: str
    expected_answer: str


class InterviewQuestionGenerator:
    async def generate_questions(
        self,
        *,
        interview_type: InterviewType,
        difficulty: InterviewDifficulty,
        skills: list[str],
        resume_summary: str | None,
        count: int,
    ) -> list[GeneratedQuestion]:
        if settings.openai_api_key:
            try:
                return await self._generate_with_openai(
                    interview_type=interview_type,
                    difficulty=difficulty,
                    skills=skills,
                    resume_summary=resume_summary,
                    count=count,
                )
            except Exception:
                return self._generate_fallback(interview_type, difficulty, skills, count)
        return self._generate_fallback(interview_type, difficulty, skills, count)

    async def _generate_with_openai(
        self,
        *,
        interview_type: InterviewType,
        difficulty: InterviewDifficulty,
        skills: list[str],
        resume_summary: str | None,
        count: int,
    ) -> list[GeneratedQuestion]:
        prompt = (
            "Generate interview questions as strict JSON array. Each item must contain "
            "'question' and 'expected_answer'. "
            f"Type: {interview_type.value}. Difficulty: {difficulty.value}. "
            f"Skills: {', '.join(skills) or 'general candidate profile'}. "
            f"Resume summary: {resume_summary or 'not available'}. "
            f"Question count: {count}."
        )
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{settings.openai_base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json={
                    "model": settings.openai_model,
                    "messages": [
                        {"role": "system", "content": "You create concise, job-relevant interview questions."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.4,
                },
            )
            response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return self._coerce_questions(parsed, count)

    def _generate_fallback(
        self,
        interview_type: InterviewType,
        difficulty: InterviewDifficulty,
        skills: list[str],
        count: int,
    ) -> list[GeneratedQuestion]:
        focus_skills = skills[:count] or ["communication", "problem solving", "role readiness"]
        templates = {
            InterviewType.technical: (
                "How would you apply {skill} to solve a production backend problem?",
                "A strong answer explains the approach, trade-offs, edge cases, and validation strategy.",
            ),
            InterviewType.hr: (
                "Tell me about a time you demonstrated {skill} in a professional setting.",
                "A strong answer uses a clear situation, action, result, and reflection.",
            ),
            InterviewType.behavioral: (
                "Describe a challenging situation where {skill} helped you make progress.",
                "A strong answer shows ownership, collaboration, measurable impact, and learning.",
            ),
            InterviewType.aptitude: (
                "Walk through how you would reason about a {skill} problem under time pressure.",
                "A strong answer breaks the problem down logically and checks assumptions.",
            ),
        }
        question_template, answer_template = templates[interview_type]
        generated: list[GeneratedQuestion] = []
        for index in range(count):
            skill = focus_skills[index % len(focus_skills)]
            generated.append(
                {
                    "question": f"{question_template.format(skill=skill)} ({difficulty.value})",
                    "expected_answer": answer_template,
                }
            )
        return generated

    @staticmethod
    def _coerce_questions(raw: object, count: int) -> list[GeneratedQuestion]:
        if not isinstance(raw, list):
            raise ValueError("AI response must be a JSON array")
        questions = []
        for item in raw[:count]:
            if not isinstance(item, dict):
                continue
            question = str(item.get("question", "")).strip()
            expected_answer = str(item.get("expected_answer", "")).strip()
            if question and expected_answer:
                questions.append({"question": question, "expected_answer": expected_answer})
        if not questions:
            raise ValueError("AI response did not include usable questions")
        return questions
