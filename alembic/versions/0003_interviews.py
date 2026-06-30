"""ai interview generation and sessions

Revision ID: 0003_interviews
Revises: 0002_resumes
Create Date: 2026-07-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_interviews"
down_revision: str | None = "0002_resumes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    interview_type = postgresql.ENUM("technical", "hr", "behavioral", "aptitude", name="interviewtype", create_type=False)
    interview_difficulty = postgresql.ENUM("easy", "medium", "hard", name="interviewdifficulty", create_type=False)
    interview_status = postgresql.ENUM(
        "created",
        "in_progress",
        "completed",
        "cancelled",
        name="interviewstatus",
        create_type=False,
    )
    interview_type.create(op.get_bind(), checkfirst=True)
    interview_difficulty.create(op.get_bind(), checkfirst=True)
    interview_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "interview_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resume_id", sa.Integer(), sa.ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("interview_type", interview_type, nullable=False),
        sa.Column("difficulty", interview_difficulty, nullable=False),
        sa.Column("status", interview_status, nullable=False),
        sa.Column("question_count", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_interview_sessions_id", "interview_sessions", ["id"])
    op.create_index("ix_interview_sessions_user_id", "interview_sessions", ["user_id"])

    op.create_table(
        "interview_questions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "interview_id",
            sa.Integer(),
            sa.ForeignKey("interview_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("category", interview_type, nullable=False),
        sa.Column("difficulty", interview_difficulty, nullable=False),
        sa.Column("expected_answer", sa.Text(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_interview_questions_id", "interview_questions", ["id"])
    op.create_index("ix_interview_questions_interview_id", "interview_questions", ["interview_id"])


def downgrade() -> None:
    op.drop_index("ix_interview_questions_interview_id", table_name="interview_questions")
    op.drop_index("ix_interview_questions_id", table_name="interview_questions")
    op.drop_table("interview_questions")
    op.drop_index("ix_interview_sessions_user_id", table_name="interview_sessions")
    op.drop_index("ix_interview_sessions_id", table_name="interview_sessions")
    op.drop_table("interview_sessions")
    postgresql.ENUM(name="interviewstatus").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="interviewdifficulty").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="interviewtype").drop(op.get_bind(), checkfirst=True)
