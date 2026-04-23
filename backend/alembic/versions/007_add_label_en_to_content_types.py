"""Add label_en column to content_types table.

Revision ID: 007
Revises: 006
Create Date: 2026-04-23
"""

from alembic import op
import sqlalchemy as sa

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "content_types",
        sa.Column("label_en", sa.String(100), nullable=True),
    )

    op.execute("""
        UPDATE content_types SET label_en = 'Place'   WHERE key = 'place';
        UPDATE content_types SET label_en = 'Event'   WHERE key = 'event';
        UPDATE content_types SET label_en = 'Tips'    WHERE key = 'tips';
        UPDATE content_types SET label_en = 'Review'  WHERE key = 'review';
        UPDATE content_types SET label_en = 'Other'   WHERE key = 'unknown';
    """)


def downgrade() -> None:
    op.drop_column("content_types", "label_en")
