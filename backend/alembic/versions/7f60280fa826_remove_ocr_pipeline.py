"""remove_ocr_pipeline

Revision ID: 7f60280fa826
Revises: b2c3d4e5f6a1
Create Date: 2026-04-20

Drop the llm_document_jobs table and ocr_extracted column from ap.invoices.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '7f60280fa826'
down_revision: Union[str, None] = 'b2c3d4e5f6a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop OCR jobs table
    op.execute("DROP TABLE IF EXISTS mlops.llm_document_jobs CASCADE")

    # Drop ocr_extracted column from ap.invoices
    op.drop_column('invoices', 'ocr_extracted', schema='ap')


def downgrade() -> None:
    # Restore ocr_extracted column
    op.add_column(
        'invoices',
        sa.Column('ocr_extracted', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        schema='ap',
    )

    # Restore llm_document_jobs table
    op.execute("""
        CREATE TABLE IF NOT EXISTS mlops.llm_document_jobs (
            id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            document_type  VARCHAR(50)  NOT NULL,
            document_id    VARCHAR(100),
            file_path      VARCHAR(500),
            file_name      VARCHAR(200),
            status         VARCHAR(20)  NOT NULL DEFAULT 'pending',
            extracted_data JSONB,
            error_message  TEXT,
            model_used     VARCHAR(100),
            input_tokens   INTEGER,
            output_tokens  INTEGER,
            triggered_by   VARCHAR(100),
            started_at     TIMESTAMPTZ,
            finished_at    TIMESTAMPTZ,
            created_at     TIMESTAMPTZ  NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_llm_document_jobs_document_id
        ON mlops.llm_document_jobs (document_id)
    """)
