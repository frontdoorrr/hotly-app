"""Create user_tags table for tag statistics

Revision ID: 003
Revises: 002
Create Date: 2025-01-17 10:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create user_tags table for efficient tag statistics."""

    # Enable pg_trgm extension for trigram similarity search
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # Create user_tags table
    op.create_table(
        "user_tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tag", sa.String(50), nullable=False),
        sa.Column("usage_count", sa.Integer, nullable=False, server_default="1"),
        sa.Column(
            "last_used",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "category_distribution",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    # Create unique constraint for user_id + tag combination
    op.create_unique_constraint(
        "uq_user_tags_user_tag", "user_tags", ["user_id", "tag"]
    )

    # Create indexes for optimal performance

    # Index for user's most used tags (sorted by usage count)
    op.create_index(
        "idx_user_tags_user_usage",
        "user_tags",
        ["user_id", sa.text("usage_count DESC")],
    )

    # Trigram GIN index for fuzzy tag search/autocomplete
    op.execute(
        "CREATE INDEX idx_user_tags_tag_trgm ON user_tags "
        "USING GIN (tag gin_trgm_ops)"
    )

    # Index for last_used queries (e.g., recent tags)
    op.create_index(
        "idx_user_tags_last_used", "user_tags", ["user_id", "last_used"]
    )

    # Create trigger for updating updated_at timestamp
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_user_tags_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE TRIGGER trigger_user_tags_updated_at
        BEFORE UPDATE ON user_tags
        FOR EACH ROW
        EXECUTE FUNCTION update_user_tags_updated_at();
        """
    )


def downgrade() -> None:
    """Drop user_tags table and related objects."""

    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS trigger_user_tags_updated_at ON user_tags")
    op.execute("DROP FUNCTION IF EXISTS update_user_tags_updated_at")

    # Drop indexes
    op.drop_index("idx_user_tags_last_used")
    op.execute("DROP INDEX IF EXISTS idx_user_tags_tag_trgm")
    op.drop_index("idx_user_tags_user_usage")

    # Drop unique constraint
    op.drop_constraint("uq_user_tags_user_tag", "user_tags", type_="unique")

    # Drop table
    op.drop_table("user_tags")

    # Note: We don't drop pg_trgm extension as it might be used elsewhere
