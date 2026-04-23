"""Add GIN indexes on ARRAY columns of archived_contents.

Revision ID: 006
Revises: 005
Create Date: 2026-04-23
"""

from alembic import op

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_archived_contents_keywords_main_gin
        ON archived_contents USING GIN(keywords_main)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_archived_contents_topic_categories_gin
        ON archived_contents USING GIN(topic_categories)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_archived_contents_named_entities_gin
        ON archived_contents USING GIN(named_entities)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_archived_contents_keywords_sub_gin
        ON archived_contents USING GIN(keywords_sub)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_archived_contents_keywords_main_gin")
    op.execute("DROP INDEX IF EXISTS ix_archived_contents_topic_categories_gin")
    op.execute("DROP INDEX IF EXISTS ix_archived_contents_named_entities_gin")
    op.execute("DROP INDEX IF EXISTS ix_archived_contents_keywords_sub_gin")
