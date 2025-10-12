"""Create places table with PostGIS support

Revision ID: 001
Revises:
Create Date: 2025-01-03 12:00:00.000000

"""
import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create places table with PostGIS support."""

    # Enable PostGIS extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # Create places table
    op.create_table(
        "places",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("opening_hours", sa.Text, nullable=True),
        sa.Column("price_range", sa.String(50), nullable=True),
        sa.Column("category", sa.String(50), nullable=False, server_default="other"),
        sa.Column("tags", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("keywords", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column(
            "coordinates", geoalchemy2.Geography("POINT", srid=4326), nullable=True
        ),
        sa.Column("ai_confidence", sa.Float, nullable=True),
        sa.Column("ai_model_version", sa.String(100), nullable=True),
        sa.Column("recommendation_score", sa.Integer, nullable=True),
        sa.Column("source_url", sa.String(1000), nullable=True),
        sa.Column("source_platform", sa.String(50), nullable=True),
        sa.Column("source_content_hash", sa.String(64), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    # Create indexes for optimal performance

    # Basic indexes
    op.create_index("idx_places_user_id", "places", ["user_id"])
    op.create_index("idx_places_status", "places", ["status", "created_at"])
    op.create_index("idx_places_source_hash", "places", ["source_content_hash"])

    # Composite indexes for common queries
    op.create_index(
        "idx_places_user_category_created",
        "places",
        ["user_id", "category", "created_at"],
    )

    # GiST spatial index for geographical queries
    op.execute(
        "CREATE INDEX idx_places_coordinates_gist ON places " "USING GIST (coordinates)"
    )

    # GIN indexes for array and text search
    op.execute("CREATE INDEX idx_places_tags_gin ON places " "USING GIN (tags)")

    # Full-text search index for name and address
    op.execute(
        "CREATE INDEX idx_places_search_gin ON places "
        "USING GIN (to_tsvector('simple', "
        "COALESCE(name, '') || ' ' || COALESCE(address, '')))"
    )

    # Recommendation ranking index
    op.create_index(
        "idx_places_recommendation",
        "places",
        ["category", "recommendation_score", "ai_confidence"],
    )

    # Duplicate detection index
    op.create_index(
        "idx_places_duplicate", "places", ["user_id", "source_content_hash"]
    )


def downgrade() -> None:
    """Drop places table and related indexes."""

    # Drop indexes first
    op.drop_index("idx_places_duplicate")
    op.drop_index("idx_places_recommendation")
    op.execute("DROP INDEX IF EXISTS idx_places_search_gin")
    op.execute("DROP INDEX IF EXISTS idx_places_tags_gin")
    op.execute("DROP INDEX IF EXISTS idx_places_coordinates_gist")
    op.drop_index("idx_places_user_category_created")
    op.drop_index("idx_places_source_hash")
    op.drop_index("idx_places_status")
    op.drop_index("idx_places_user_id")

    # Drop table
    op.drop_table("places")

    # Note: We don't drop PostGIS extension as it might be used by other tables
