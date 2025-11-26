"""Create user tables for PostgreSQL

Revision ID: 002
Revises: 001
Create Date: 2025-01-25 12:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create user, user_preferences, and user_settings tables."""

    # Create user table
    op.create_table(
        "user",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("firebase_uid", sa.String(128), unique=True, index=True, nullable=True),
        sa.Column("full_name", sa.String, index=True, nullable=True),
        sa.Column("email", sa.String, unique=True, index=True, nullable=False),
        sa.Column("hashed_password", sa.String, nullable=False),
        sa.Column("nickname", sa.String(50), nullable=True),
        sa.Column("profile_image_url", sa.String(500), nullable=True),
        sa.Column("bio", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("is_superuser", sa.Boolean, default=False),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # Create user_preferences table
    op.create_table(
        "user_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("categories", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("category_weights", postgresql.JSON, nullable=False, server_default="{}"),
        sa.Column("food_preferences", postgresql.JSON, nullable=True, server_default="{}"),
        sa.Column("atmosphere_preferences", postgresql.JSON, nullable=True, server_default="{}"),
        sa.Column("location_preferences", postgresql.JSON, nullable=True),
        sa.Column("max_travel_distance_km", sa.Integer, server_default="10"),
        sa.Column("budget_level", sa.String(20), nullable=False, server_default="'medium'"),
        sa.Column("budget_ranges", postgresql.JSON, nullable=True),
        sa.Column("budget_flexibility", sa.String(20), server_default="'medium'"),
        sa.Column("companion_type", sa.String(20), nullable=False, server_default="'couple'"),
        sa.Column("group_size_preference", sa.Integer, server_default="2"),
        sa.Column("social_comfort_level", sa.String(20), server_default="'medium'"),
        sa.Column("activity_intensity", sa.String(20), server_default="'moderate'"),
        sa.Column("physical_limitations", postgresql.JSON, server_default="[]"),
        sa.Column("time_preferences", postgresql.JSON, nullable=True),
        sa.Column("quality_score", sa.Float, server_default="0.0"),
        sa.Column("preferences_complete", sa.Boolean, server_default="false"),
        sa.Column("last_survey_completed", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # Create user_settings table
    op.create_table(
        "user_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True, index=True),
        sa.Column("push_enabled", sa.Boolean, server_default="true"),
        sa.Column("email_enabled", sa.Boolean, server_default="true"),
        sa.Column("sms_enabled", sa.Boolean, server_default="false"),
        sa.Column("marketing_notifications", sa.Boolean, server_default="true"),
        sa.Column("recommendation_notifications", sa.Boolean, server_default="true"),
        sa.Column("social_notifications", sa.Boolean, server_default="true"),
        sa.Column("profile_visibility", sa.String(20), server_default="'public'"),
        sa.Column("activity_visibility", sa.Boolean, server_default="true"),
        sa.Column("show_saved_places", sa.Boolean, server_default="true"),
        sa.Column("allow_friend_requests", sa.Boolean, server_default="true"),
        sa.Column("language", sa.String(10), server_default="'ko'"),
        sa.Column("theme", sa.String(20), server_default="'system'"),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # Create indexes
    op.create_index("idx_user_email", "user", ["email"])
    op.create_index("idx_user_firebase_uid", "user", ["firebase_uid"])
    op.create_index("idx_user_preferences_user_id", "user_preferences", ["user_id"])
    op.create_index("idx_user_settings_user_id", "user_settings", ["user_id"])

    # Create trigger function for updating updated_at timestamp
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    # Create triggers for updated_at
    op.execute(
        """
        CREATE TRIGGER update_user_updated_at
        BEFORE UPDATE ON "user"
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
        """
    )

    op.execute(
        """
        CREATE TRIGGER update_user_preferences_updated_at
        BEFORE UPDATE ON user_preferences
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
        """
    )

    op.execute(
        """
        CREATE TRIGGER update_user_settings_updated_at
        BEFORE UPDATE ON user_settings
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
        """
    )


def downgrade() -> None:
    """Drop user tables."""

    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_user_settings_updated_at ON user_settings")
    op.execute("DROP TRIGGER IF EXISTS update_user_preferences_updated_at ON user_preferences")
    op.execute("DROP TRIGGER IF EXISTS update_user_updated_at ON \"user\"")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")

    # Drop indexes
    op.drop_index("idx_user_settings_user_id")
    op.drop_index("idx_user_preferences_user_id")
    op.drop_index("idx_user_firebase_uid")
    op.drop_index("idx_user_email")

    # Drop tables
    op.drop_table("user_settings")
    op.drop_table("user_preferences")
    op.drop_table("user")
