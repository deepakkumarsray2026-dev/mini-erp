"""
LLMOps API — Phase 3 RAG + LLM endpoints.

Prefix: /api/v1/llmops

  Chat:
    POST   /chat/conversations              — Create conversation
    GET    /chat/conversations              — List user's conversations
    GET    /chat/conversations/{id}         — Get conversation + messages
    DELETE /chat/conversations/{id}         — Archive conversation
    POST   /chat/conversations/{id}/message — Send message

  Duplicate Invoice Detection:
    POST   /embeddings/reindex              — Reindex all invoices (admin)
    POST   /invoices/{id}/duplicate-check  — Check a single invoice
    GET    /invoices/duplicates            — List flagged duplicates

  OCR:
    POST   /ocr/upload                     — Upload document, returns job_id
    GET    /ocr/jobs                       — List OCR jobs
    GET    /ocr/jobs/{job_id}              — Get job status + results
"""
import os
import shutil
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.permissions import ModuleName, can_read, can_run, get_current_user
from app.models.llmops import LLMChatMessage, LLMConversation, LLMDocumentJob
from app.services import ai_service

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ConversationOut(BaseModel):
    id:              str
    title:           str | None
    status:          str
    created_at:      datetime
    last_message_at: datetime | None

    class Config:
        from_attributes = True


class MessageOut(BaseModel):
    id:            str
    role:          str
    content:       str
    sql_query:     str | None = None
    sql_results:   Any        = None
    input_tokens:  int | None = None
    output_tokens: int | None = None
    latency_ms:    int | None = None
    created_at:    datetime

    class Config:
        from_attributes = True


class ConversationDetailOut(ConversationOut):
    messages: list[MessageOut] = []


class SendMessageIn(BaseModel):
    content: str


class SendMessageOut(BaseModel):
    message:       MessageOut
    sql_query:     str | None = None
    sql_results:   Any        = None
    latency_ms:    int | None = None


class DuplicateCheckOut(BaseModel):
    invoice_id:   str
    is_duplicate: bool
    similar:      list[dict]
    top_match:    dict | None


class OcrJobOut(BaseModel):
    id:             str
    document_type:  str
    file_name:      str | None
    status:         str
    extracted_data: Any        = None
    error_message:  str | None = None
    model_used:     str | None = None
    input_tokens:   int | None = None
    output_tokens:  int | None = None
    created_at:     datetime
    started_at:     datetime | None = None
    finished_at:    datetime | None = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Chat — Conversations
# ---------------------------------------------------------------------------

@router.post("/chat/conversations", response_model=ConversationOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(can_run(ModuleName.AI))])
async def create_conversation(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv = await ai_service.create_conversation(current_user.id, db)
    return conv


@router.get("/chat/conversations", response_model=list[ConversationOut],
            dependencies=[Depends(can_read(ModuleName.AI))])
async def list_conversations(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ai_service.list_conversations(current_user.id, db)


@router.get("/chat/conversations/{conv_id}", response_model=ConversationDetailOut,
            dependencies=[Depends(can_read(ModuleName.AI))])
async def get_conversation(
    conv_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(LLMConversation)
        .where(LLMConversation.id == conv_id, LLMConversation.user_id == current_user.id)
        .options(selectinload(LLMConversation.messages))
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.delete("/chat/conversations/{conv_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(can_run(ModuleName.AI))])
async def delete_conversation(
    conv_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await ai_service.delete_conversation(conv_id, current_user.id, db)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")


@router.post("/chat/conversations/{conv_id}/message", response_model=SendMessageOut,
             dependencies=[Depends(can_run(ModuleName.AI))])
async def send_message(
    conv_id: str,
    body: SendMessageIn,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not body.content.strip():
        raise HTTPException(status_code=422, detail="Message content cannot be empty")
    if settings.LLM_PROVIDER == "anthropic" and not settings.ANTHROPIC_API_KEY:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")
    if settings.LLM_PROVIDER == "groq" and not settings.GROQ_API_KEY:
        raise HTTPException(status_code=503, detail="GROQ_API_KEY not configured")

    try:
        result = await ai_service.send_message(conv_id, current_user.id, body.content, db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM error: {str(exc)}")

    # Reload the assistant message for the response
    msg_result = await db.execute(
        select(LLMChatMessage)
        .where(
            LLMChatMessage.conversation_id == conv_id,
            LLMChatMessage.role == "assistant",
        )
        .order_by(LLMChatMessage.created_at.desc())
        .limit(1)
    )
    assistant_msg = msg_result.scalar_one()

    return SendMessageOut(
        message=MessageOut.model_validate(assistant_msg),
        sql_query=result.get("sql_query"),
        sql_results=result.get("sql_results"),
        latency_ms=result.get("latency_ms"),
    )


# ---------------------------------------------------------------------------
# Duplicate Invoice Detection
# ---------------------------------------------------------------------------

@router.post("/embeddings/reindex", dependencies=[Depends(can_run(ModuleName.AI))])
async def reindex_invoices(db: AsyncSession = Depends(get_db)):
    """Reindex all invoices (admin operation — may be slow)."""
    from app.ml.llm.embedding_service import reindex_all_invoices
    result = await reindex_all_invoices(db)
    return result


@router.post("/invoices/{invoice_id}/duplicate-check", response_model=DuplicateCheckOut,
             dependencies=[Depends(can_run(ModuleName.AI))])
async def check_duplicate(invoice_id: str, db: AsyncSession = Depends(get_db)):
    try:
        return await ai_service.check_invoice_duplicate(invoice_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/invoices/duplicates", dependencies=[Depends(can_read(ModuleName.AI))])
async def list_duplicates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    from app.models.ap import Invoice, Vendor
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Invoice, Vendor.name.label("vendor_name"))
        .join(Vendor, Invoice.vendor_id == Vendor.id)
        .where(Invoice.is_duplicate == True)
        .order_by(Invoice.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    rows = result.fetchall()
    items = [
        {
            "id":              inv.id,
            "invoice_number":  inv.invoice_number,
            "vendor_name":     vendor_name,
            "total_amount":    str(inv.total_amount),
            "duplicate_of_id": inv.duplicate_of_id,
            "status":          inv.status.value if hasattr(inv.status, "value") else str(inv.status),
        }
        for inv, vendor_name in rows
    ]
    return {"items": items, "page": page, "page_size": page_size}


# ---------------------------------------------------------------------------
# OCR
# ---------------------------------------------------------------------------

_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


@router.post("/ocr/upload", response_model=OcrJobOut, status_code=status.HTTP_202_ACCEPTED,
             dependencies=[Depends(can_run(ModuleName.AI))])
async def upload_for_ocr(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type '{ext}'. Allowed: {sorted(_ALLOWED_EXTENSIONS)}",
        )

    # Save to uploads directory
    upload_dir = os.path.join(settings.UPLOAD_DIR, "ocr")
    os.makedirs(upload_dir, exist_ok=True)
    safe_name = f"{uuid.uuid4()}{ext}"
    file_path  = os.path.join(upload_dir, safe_name)

    with open(file_path, "wb") as out:
        shutil.copyfileobj(file.file, out)

    job = await ai_service.create_ocr_job(
        file_path=file_path,
        file_name=file.filename or safe_name,
        triggered_by=current_user.id,
        db=db,
    )
    return job


@router.get("/ocr/jobs", dependencies=[Depends(can_read(ModuleName.AI))])
async def list_ocr_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await ai_service.list_ocr_jobs(db, page=page, page_size=page_size)


@router.get("/ocr/jobs/{job_id}", response_model=OcrJobOut,
            dependencies=[Depends(can_read(ModuleName.AI))])
async def get_ocr_job(job_id: str, db: AsyncSession = Depends(get_db)):
    job = await ai_service.get_ocr_job(job_id, db)
    if not job:
        raise HTTPException(status_code=404, detail="OCR job not found")
    return job
