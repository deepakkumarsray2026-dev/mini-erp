"""
Celery task for async invoice OCR processing.
"""
import asyncio
from datetime import datetime, timezone

from loguru import logger

from app.celery_app import celery
from app.core.database import SyncSessionLocal, AsyncSessionLocal
from app.models.llmops import LLMDocumentJob, DocumentJobStatus


@celery.task(bind=True, name="app.tasks.ocr_tasks.run_ocr_job", max_retries=2, default_retry_delay=30)
def run_ocr_job(self, job_id: str):
    """
    Runs OCR on a document and updates the LLMDocumentJob record.
    Uses sync DB access (Celery worker context).
    """
    from sqlalchemy.orm import Session

    db: Session = SyncSessionLocal()
    try:
        job = db.query(LLMDocumentJob).filter(LLMDocumentJob.id == job_id).first()
        if not job:
            logger.error(f"OCR job {job_id} not found")
            return

        job.status     = DocumentJobStatus.PROCESSING
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        # Run async OCR in sync context
        import asyncio
        from app.ml.llm.ocr_service import extract_invoice

        result = asyncio.run(extract_invoice(job.file_path))

        job.status         = DocumentJobStatus.COMPLETED
        job.extracted_data = result["extracted_data"]
        job.model_used     = result["model_used"]
        job.input_tokens   = result["input_tokens"]
        job.output_tokens  = result["output_tokens"]
        job.finished_at    = datetime.now(timezone.utc)
        db.commit()
        logger.info(f"OCR job {job_id} completed in {result['latency_ms']}ms")

    except Exception as exc:
        logger.error(f"OCR job {job_id} failed: {exc}")
        if db:
            try:
                job = db.query(LLMDocumentJob).filter(LLMDocumentJob.id == job_id).first()
                if job:
                    job.status        = DocumentJobStatus.FAILED
                    job.error_message = str(exc)
                    job.finished_at   = datetime.now(timezone.utc)
                    db.commit()
            except Exception:
                pass
        raise self.retry(exc=exc)
    finally:
        db.close()
