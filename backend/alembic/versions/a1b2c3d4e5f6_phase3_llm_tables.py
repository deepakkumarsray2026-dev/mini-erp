"""phase3_llm_tables — chat, jobs (no pgvector dependency)

Revision ID: a1b2c3d4e5f6
Revises: 123aa831b0c5
Create Date: 2026-04-20 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '123aa831b0c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # llm_conversations
    op.execute("""
        CREATE TABLE IF NOT EXISTS mlops.llm_conversations (
            id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id         UUID NOT NULL,
            title           VARCHAR(200),
            status          VARCHAR(20) NOT NULL DEFAULT 'active',
            created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            last_message_at TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_llm_conversations_user_id ON mlops.llm_conversations (user_id)")

    # llm_chat_messages
    op.execute("""
        CREATE TABLE IF NOT EXISTS mlops.llm_chat_messages (
            id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            conversation_id UUID NOT NULL REFERENCES mlops.llm_conversations(id) ON DELETE CASCADE,
            role            VARCHAR(20) NOT NULL,
            content         TEXT NOT NULL,
            sql_query       TEXT,
            sql_results     JSONB,
            context_used    JSONB,
            input_tokens    INTEGER,
            output_tokens   INTEGER,
            latency_ms      INTEGER,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_llm_chat_messages_conversation_id ON mlops.llm_chat_messages (conversation_id)")

    # llm_document_jobs
    op.execute("""
        CREATE TABLE IF NOT EXISTS mlops.llm_document_jobs (
            id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            document_type  VARCHAR(50) NOT NULL,
            document_id    VARCHAR(100),
            file_path      VARCHAR(500),
            file_name      VARCHAR(200),
            status         VARCHAR(20) NOT NULL DEFAULT 'pending',
            extracted_data JSONB,
            error_message  TEXT,
            model_used     VARCHAR(100),
            input_tokens   INTEGER,
            output_tokens  INTEGER,
            triggered_by   VARCHAR(100),
            started_at     TIMESTAMPTZ,
            finished_at    TIMESTAMPTZ,
            created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_llm_document_jobs_document_id ON mlops.llm_document_jobs (document_id)")

    op.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA mlops TO erp_user")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS mlops.llm_document_jobs CASCADE")
    op.execute("DROP TABLE IF EXISTS mlops.llm_chat_messages CASCADE")
    op.execute("DROP TABLE IF EXISTS mlops.llm_conversations CASCADE")
