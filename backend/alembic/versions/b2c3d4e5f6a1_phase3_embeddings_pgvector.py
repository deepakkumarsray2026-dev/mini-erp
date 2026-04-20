"""phase3_embeddings_pgvector — vector embeddings table (requires pgvector/pgvector:pg15 image)

Revision ID: b2c3d4e5f6a1
Revises: a1b2c3d4e5f6
Create Date: 2026-04-20 00:01:00.000000

Run this ONLY after switching the db image to pgvector/pgvector:pg15 in docker-compose.dev.yml
and recreating the db container.

"""
from typing import Sequence, Union
from alembic import op

revision: str = 'b2c3d4e5f6a1'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.execute("""
        CREATE TABLE IF NOT EXISTS mlops.llm_embeddings (
            id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            document_type   VARCHAR(50) NOT NULL,
            document_id     VARCHAR(100) NOT NULL,
            content_hash    VARCHAR(64),
            embedding_model VARCHAR(100) DEFAULT 'nomic-embed-text',
            embedding       vector(768),
            metadata        JSONB,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_llm_embeddings_document_type ON mlops.llm_embeddings (document_type)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_llm_embeddings_document_id   ON mlops.llm_embeddings (document_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_llm_embeddings_content_hash  ON mlops.llm_embeddings (content_hash)")
    op.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA mlops TO erp_user")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS mlops.llm_embeddings CASCADE")
