"""Add archived_contents table

Revision ID: 004
Revises: 003
Create Date: 2026-04-06 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ENUM 타입 생성 (DO 블록으로 중복 방지 — PostgreSQL IF NOT EXISTS는 지원 안 됨)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'platform_type') THEN
                CREATE TYPE platform_type AS ENUM ('youtube', 'instagram', 'naver_blog');
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'content_type_enum') THEN
                CREATE TYPE content_type_enum AS ENUM ('place', 'event', 'tips', 'review', 'unknown');
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sentiment_type') THEN
                CREATE TYPE sentiment_type AS ENUM ('positive', 'neutral', 'negative');
            END IF;
        END $$;
    """)

    # 테이블 생성
    op.create_table(
        "archived_contents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column(
            "platform",
            postgresql.ENUM("youtube", "instagram", "naver_blog", name="platform_type", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "content_type",
            postgresql.ENUM("place", "event", "tips", "review", "unknown", name="content_type_enum", create_type=False),
            nullable=False,
        ),
        # 메타데이터
        sa.Column("title", sa.Text, nullable=True),
        sa.Column("author", sa.String(255), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("thumbnail_url", sa.Text, nullable=True),
        sa.Column("language", sa.String(10), nullable=True),
        # 분석 공통
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("keywords_main", postgresql.ARRAY(sa.Text), nullable=True),
        sa.Column("keywords_sub", postgresql.ARRAY(sa.Text), nullable=True),
        sa.Column("named_entities", postgresql.ARRAY(sa.Text), nullable=True),
        sa.Column("topic_categories", postgresql.ARRAY(sa.Text), nullable=True),
        sa.Column(
            "sentiment",
            postgresql.ENUM("positive", "neutral", "negative", name="sentiment_type", create_type=False),
            nullable=True,
        ),
        sa.Column("todos", postgresql.ARRAY(sa.Text), nullable=True),
        sa.Column("insights", postgresql.ARRAY(sa.Text), nullable=True),
        # 타입별 데이터
        sa.Column("type_specific_data", postgresql.JSONB, nullable=True),
        # 앱 메타
        sa.Column("link_analyzer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "archived_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # 인덱스
    op.create_index("ix_archived_contents_user_id", "archived_contents", ["user_id"])
    op.create_index(
        "ix_archived_contents_user_content_type",
        "archived_contents",
        ["user_id", "content_type"],
    )
    op.create_index(
        "ix_archived_contents_user_archived_at",
        "archived_contents",
        ["user_id", sa.text("archived_at DESC")],
    )
    op.create_index("ix_archived_contents_url", "archived_contents", ["url"])


def downgrade() -> None:
    op.drop_index("ix_archived_contents_url", table_name="archived_contents")
    op.drop_index("ix_archived_contents_user_archived_at", table_name="archived_contents")
    op.drop_index("ix_archived_contents_user_content_type", table_name="archived_contents")
    op.drop_index("ix_archived_contents_user_id", table_name="archived_contents")
    op.drop_table("archived_contents")

    op.execute("DROP TYPE IF EXISTS sentiment_type")
    op.execute("DROP TYPE IF EXISTS content_type_enum")
    op.execute("DROP TYPE IF EXISTS platform_type")
