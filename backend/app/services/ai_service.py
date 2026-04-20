"""
AI service — thin orchestration layer for Phase 3 LLM/RAG features.

Coordinates between the API layer, LLM services, and the database.
"""
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.llmops import (
    ConversationStatus,
    DocumentJobStatus,
    LLMChatMessage,
    LLMConversation,
    LLMDocumentJob,
)


# ---------------------------------------------------------------------------
# Conversation management
# ---------------------------------------------------------------------------

async def create_conversation(user_id: str, db: AsyncSession) -> LLMConversation:
    conv = LLMConversation(user_id=user_id, title="New conversation")
    db.add(conv)
    await db.flush()
    return conv


async def get_conversation(conv_id: str, user_id: str, db: AsyncSession) -> LLMConversation | None:
    result = await db.execute(
        select(LLMConversation).where(
            LLMConversation.id      == conv_id,
            LLMConversation.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def list_conversations(user_id: str, db: AsyncSession) -> list[LLMConversation]:
    result = await db.execute(
        select(LLMConversation)
        .where(
            LLMConversation.user_id == user_id,
            LLMConversation.status  == ConversationStatus.ACTIVE,
        )
        .order_by(LLMConversation.last_message_at.desc().nullsfirst())
        .limit(50)
    )
    return list(result.scalars().all())


async def delete_conversation(conv_id: str, user_id: str, db: AsyncSession) -> bool:
    conv = await get_conversation(conv_id, user_id, db)
    if not conv:
        return False
    conv.status = ConversationStatus.ARCHIVED
    await db.flush()
    return True


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

async def send_message(
    conv_id: str,
    user_id: str,
    content: str,
    db: AsyncSession,
) -> dict:
    """Process a user message, call the LLM, persist both turns, and return the result."""
    from app.ml.llm.chat_service import chat, generate_title

    conv = await get_conversation(conv_id, user_id, db)
    if not conv:
        raise ValueError(f"Conversation {conv_id} not found")

    # Persist user message
    user_msg = LLMChatMessage(
        conversation_id=conv_id,
        role="user",
        content=content,
    )
    db.add(user_msg)
    await db.flush()

    # Call LLM
    result = await chat(conv_id, content, db)

    # Persist assistant reply
    assistant_msg = LLMChatMessage(
        conversation_id=conv_id,
        role="assistant",
        content=result["content"],
        sql_query=result.get("sql_query"),
        sql_results=result.get("sql_results"),
        input_tokens=result.get("input_tokens"),
        output_tokens=result.get("output_tokens"),
        latency_ms=result.get("latency_ms"),
    )
    db.add(assistant_msg)

    # Update conversation timestamp + generate title on first exchange
    conv.last_message_at = datetime.now(timezone.utc)
    if conv.title == "New conversation":
        conv.title = await generate_title(content)

    await db.flush()
    return result


# ---------------------------------------------------------------------------
# Duplicate invoice detection
# ---------------------------------------------------------------------------

async def check_invoice_duplicate(invoice_id: str, db: AsyncSession) -> dict:
    """Embed the invoice and find similar ones. Flags it if similarity >= 0.92."""
    from app.models.ap import Invoice, Vendor
    from app.ml.llm.embedding_service import upsert_invoice_embedding, find_similar_invoices

    result = await db.execute(
        select(Invoice, Vendor.name.label("vendor_name"))
        .join(Vendor, Invoice.vendor_id == Vendor.id)
        .where(Invoice.id == invoice_id)
    )
    row = result.first()
    if not row:
        raise ValueError(f"Invoice {invoice_id} not found")

    inv, vendor_name = row
    invoice_dict = {
        "invoice_id":     inv.id,
        "invoice_number": inv.invoice_number,
        "vendor_name":    vendor_name,
        "description":    inv.description,
        "total_amount":   str(inv.total_amount),
        "invoice_date":   str(inv.invoice_date) if inv.invoice_date else None,
    }

    await upsert_invoice_embedding(invoice_id, invoice_dict, db)
    similar = await find_similar_invoices(invoice_id, invoice_dict, db, threshold=0.12)

    is_duplicate = any(s["similarity"] >= 0.92 for s in similar)
    top_match = similar[0] if similar else None

    if is_duplicate and top_match:
        inv.is_duplicate    = True
        inv.duplicate_of_id = top_match["invoice_id"]
        await db.flush()

    return {
        "invoice_id":   invoice_id,
        "is_duplicate": is_duplicate,
        "similar":      similar,
        "top_match":    top_match,
    }


# ---------------------------------------------------------------------------
# OCR
# ---------------------------------------------------------------------------

async def create_ocr_job(
    file_path: str,
    file_name: str,
    triggered_by: str,
    db: AsyncSession,
) -> LLMDocumentJob:
    """Create an OCR job record and enqueue the Celery task."""
    from app.tasks.ocr_tasks import run_ocr_job

    job = LLMDocumentJob(
        document_type="invoice_ocr",
        file_path=file_path,
        file_name=file_name,
        status=DocumentJobStatus.PENDING,
        triggered_by=triggered_by,
    )
    db.add(job)
    await db.flush()

    run_ocr_job.delay(job.id)
    logger.info(f"OCR job {job.id} enqueued for {file_name}")
    return job


async def get_ocr_job(job_id: str, db: AsyncSession) -> LLMDocumentJob | None:
    result = await db.execute(
        select(LLMDocumentJob).where(LLMDocumentJob.id == job_id)
    )
    return result.scalar_one_or_none()


async def list_ocr_jobs(db: AsyncSession, page: int = 1, page_size: int = 20) -> dict:
    offset = (page - 1) * page_size
    result = await db.execute(
        select(LLMDocumentJob)
        .where(LLMDocumentJob.document_type == "invoice_ocr")
        .order_by(LLMDocumentJob.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    jobs = list(result.scalars().all())
    return {"items": jobs, "page": page, "page_size": page_size}
