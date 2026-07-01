"""candidate answers and interview media

Revision ID: 0004_candidate_answers
Revises: 0003_interviews
Create Date: 2026-07-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_candidate_answers"
down_revision: str | None = "0003_interviews"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "candidate_answers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "interview_id",
            sa.Integer(),
            sa.ForeignKey("interview_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "question_id",
            sa.Integer(),
            sa.ForeignKey("interview_questions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("transcript", sa.Text(), nullable=False),
        sa.Column("audio_path", sa.String(length=500), nullable=True),
        sa.Column("video_path", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("interview_id", "question_id", name="uq_candidate_answers_interview_question"),
    )
    op.create_index("ix_candidate_answers_id", "candidate_answers", ["id"])
    op.create_index("ix_candidate_answers_interview_id", "candidate_answers", ["interview_id"])
    op.create_index("ix_candidate_answers_question_id", "candidate_answers", ["question_id"])


def downgrade() -> None:
    op.drop_index("ix_candidate_answers_question_id", table_name="candidate_answers")
    op.drop_index("ix_candidate_answers_interview_id", table_name="candidate_answers")
    op.drop_index("ix_candidate_answers_id", table_name="candidate_answers")
    op.drop_table("candidate_answers")
