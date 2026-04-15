"""add scores_awarded and organizer_reviews

Revision ID: 001_rating_system
Revises:
Create Date: 2026-04-15
"""
from alembic import op
import sqlalchemy as sa

revision = "001_rating_system"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Флаг: очки за гонку уже начислены
    op.add_column(
        "races",
        sa.Column("scores_awarded", sa.Boolean(), nullable=False, server_default="false"),
    )

    # Таблица отзывов об организаторе
    op.create_table(
        "organizer_reviews",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("race_id", sa.Integer(), sa.ForeignKey("races.id"), nullable=False),
        sa.Column("voter_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("organizer_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("vote", sa.Integer(), nullable=False),
        sa.UniqueConstraint("race_id", "voter_id", name="uq_review_race_voter"),
    )


def downgrade() -> None:
    op.drop_table("organizer_reviews")
    op.drop_column("races", "scores_awarded")