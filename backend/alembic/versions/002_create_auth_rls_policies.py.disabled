"""Create authentication tables and RLS policies

Revision ID: 002
Revises: 001
Create Date: 2025-01-03 14:00:00.000000

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
    """Create authentication tables and Row Level Security policies."""

    # Create user_profiles table
    op.create_table(
        "user_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("profile_image_url", sa.String(1000), nullable=True),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("linked_providers", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("is_anonymous", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_disabled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("role", sa.String(50), nullable=False, server_default="user"),
        sa.Column("permissions", postgresql.JSONB, nullable=True, server_default="{}"),
        sa.Column(
            "user_metadata", postgresql.JSONB, nullable=True, server_default="{}"
        ),
        sa.Column("app_metadata", postgresql.JSONB, nullable=True, server_default="{}"),
        sa.Column("preferred_language", sa.String(10), server_default="ko"),
        sa.Column("timezone", sa.String(50), server_default="Asia/Seoul"),
        sa.Column(
            "location", postgresql.JSONB, nullable=True
        ),  # {lat: float, lng: float}
        sa.Column("interests", postgresql.ARRAY(sa.String), nullable=True),
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
        sa.Column("last_login_at", sa.DateTime, nullable=True),
    )

    # Create guest_data table for anonymous users
    op.create_table(
        "guest_data",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("device_id", sa.String(255), nullable=False, unique=True),
        sa.Column("device_info", postgresql.JSONB, nullable=True),
        sa.Column("session_data", postgresql.JSONB, nullable=True),
        sa.Column(
            "expires_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP + INTERVAL '7 days'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    # Create user_sessions table
    op.create_table(
        "user_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_id", sa.String(255), nullable=False),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("location", postgresql.JSONB, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "expires_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP + INTERVAL '24 hours'"),
        ),
        sa.Column("last_activity_at", sa.DateTime, nullable=True),
    )

    # Create indexes
    op.create_index("idx_user_profiles_email", "user_profiles", ["email"])
    op.create_index("idx_user_profiles_provider", "user_profiles", ["provider"])
    op.create_index("idx_user_profiles_role", "user_profiles", ["role"])
    op.create_index("idx_guest_data_device_id", "guest_data", ["device_id"])
    op.create_index("idx_guest_data_expires_at", "guest_data", ["expires_at"])
    op.create_index("idx_user_sessions_user_id", "user_sessions", ["user_id"])
    op.create_index(
        "idx_user_sessions_active", "user_sessions", ["user_id", "is_active"]
    )

    # Enable Row Level Security (RLS)
    op.execute("ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE guest_data ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE places ENABLE ROW LEVEL SECURITY")

    # RLS Policy 1: Users can only view and update their own profile
    op.execute(
        """
        CREATE POLICY user_profiles_select_policy ON user_profiles
        FOR SELECT
        USING (auth.uid() = id)
    """
    )

    op.execute(
        """
        CREATE POLICY user_profiles_update_policy ON user_profiles
        FOR UPDATE
        USING (auth.uid() = id)
    """
    )

    # RLS Policy 2: Guest data access based on device_id or expiration
    op.execute(
        """
        CREATE POLICY guest_data_select_policy ON guest_data
        FOR SELECT
        USING (
            device_id = current_setting('app.device_id', true)
            OR expires_at > NOW()
        )
    """
    )

    op.execute(
        """
        CREATE POLICY guest_data_insert_policy ON guest_data
        FOR INSERT
        WITH CHECK (true)
    """
    )

    op.execute(
        """
        CREATE POLICY guest_data_update_policy ON guest_data
        FOR UPDATE
        USING (device_id = current_setting('app.device_id', true))
    """
    )

    # RLS Policy 3: Admin role can access all user data
    op.execute(
        """
        CREATE POLICY admin_full_access_policy ON user_profiles
        FOR ALL
        USING (
            EXISTS (
                SELECT 1 FROM user_profiles
                WHERE id = auth.uid()
                AND role = 'admin'
            )
        )
    """
    )

    # RLS Policy 4: Users can only access their own sessions
    op.execute(
        """
        CREATE POLICY user_sessions_select_policy ON user_sessions
        FOR SELECT
        USING (auth.uid() = user_id)
    """
    )

    op.execute(
        """
        CREATE POLICY user_sessions_insert_policy ON user_sessions
        FOR INSERT
        WITH CHECK (auth.uid() = user_id)
    """
    )

    op.execute(
        """
        CREATE POLICY user_sessions_update_policy ON user_sessions
        FOR UPDATE
        USING (auth.uid() = user_id)
    """
    )

    # RLS Policy 5: Users can only access their own places
    op.execute(
        """
        CREATE POLICY places_select_policy ON places
        FOR SELECT
        USING (auth.uid() = user_id)
    """
    )

    op.execute(
        """
        CREATE POLICY places_insert_policy ON places
        FOR INSERT
        WITH CHECK (auth.uid() = user_id)
    """
    )

    op.execute(
        """
        CREATE POLICY places_update_policy ON places
        FOR UPDATE
        USING (auth.uid() = user_id)
    """
    )

    op.execute(
        """
        CREATE POLICY places_delete_policy ON places
        FOR DELETE
        USING (auth.uid() = user_id)
    """
    )

    # Create function to automatically update updated_at timestamp
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
        CREATE TRIGGER update_user_profiles_updated_at
        BEFORE UPDATE ON user_profiles
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """
    )

    op.execute(
        """
        CREATE TRIGGER update_places_updated_at
        BEFORE UPDATE ON places
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """
    )


def downgrade() -> None:
    """Drop authentication tables and RLS policies."""

    # Drop triggers
    op.execute(
        "DROP TRIGGER IF EXISTS update_user_profiles_updated_at ON user_profiles"
    )
    op.execute("DROP TRIGGER IF EXISTS update_places_updated_at ON places")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")

    # Disable RLS
    op.execute("ALTER TABLE places DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE user_sessions DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE guest_data DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE user_profiles DISABLE ROW LEVEL SECURITY")

    # Drop indexes
    op.drop_index("idx_user_sessions_active")
    op.drop_index("idx_user_sessions_user_id")
    op.drop_index("idx_guest_data_expires_at")
    op.drop_index("idx_guest_data_device_id")
    op.drop_index("idx_user_profiles_role")
    op.drop_index("idx_user_profiles_provider")
    op.drop_index("idx_user_profiles_email")

    # Drop tables
    op.drop_table("user_sessions")
    op.drop_table("guest_data")
    op.drop_table("user_profiles")
