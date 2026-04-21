"""Add content_types table and migrate content_type column to string.

Revision ID: 005
Revises: 004
Create Date: 2026-04-21
"""

from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. content_types 테이블 생성
    op.create_table(
        "content_types",
        sa.Column("key", sa.String(50), primary_key=True),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("icon", sa.String(100), nullable=True),
        sa.Column("color", sa.String(20), nullable=True),
        sa.Column("order", sa.Integer, nullable=False, default=0),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
    )

    # 2. 초기 데이터 시드
    op.execute("""
        INSERT INTO content_types (key, label, icon, color, "order", is_active) VALUES
        ('place',   '장소',   'place',     '#FF9800', 1, true),
        ('event',   '이벤트', 'event',     '#9C27B0', 2, true),
        ('tips',    '팁',     'lightbulb', '#FFC107', 3, true),
        ('review',  '리뷰',   'star',      '#2196F3', 4, true),
        ('unknown', '기타',   'article',   '#9E9E9E', 5, false)
    """)

    # 3. archived_contents.content_type: PostgreSQL Enum → VARCHAR
    #    USING 캐스트로 기존 enum 값을 그대로 문자열로 변환
    op.execute("""
        ALTER TABLE archived_contents
        ALTER COLUMN content_type TYPE VARCHAR(50)
        USING content_type::VARCHAR(50)
    """)

    # 4. 기존 enum 타입 제거
    op.execute("DROP TYPE IF EXISTS content_type_enum")


def downgrade() -> None:
    # enum 타입 재생성
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'content_type_enum') THEN
                CREATE TYPE content_type_enum AS ENUM
                    ('place', 'event', 'tips', 'review', 'unknown');
            END IF;
        END $$
    """)

    op.execute("""
        ALTER TABLE archived_contents
        ALTER COLUMN content_type TYPE content_type_enum
        USING content_type::content_type_enum
    """)

    op.drop_table("content_types")
