"""
Embedding service — generates and stores vector embeddings for invoice deduplication.

Provider-agnostic:
  - LLM_PROVIDER=ollama  → nomic-embed-text via Ollama (dim=768, no key)
  - LLM_PROVIDER=groq    → nomic-embed-text via Ollama (embeddings always local)
  - OPENAI_API_KEY set   → text-embedding-3-small (dim=1536, requires EMBEDDING_DIM=1536)

Embeddings are stored in mlops.llm_embeddings via pgvector.
Similarity search uses cosine distance (<=>).
"""
import hashlib
import json

from loguru import logger
from openai import AsyncOpenAI
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.llmops import LLMEmbedding


def _content_hash(text_: str) -> str:
    return hashlib.sha256(text_.encode()).hexdigest()


def _get_embed_client() -> tuple[AsyncOpenAI, str]:
    """Return (client, model_name) for embeddings based on config."""
    if settings.OPENAI_API_KEY and settings.EMBEDDING_MODEL != "nomic-embed-text":
        # Use OpenAI if key is set and model differs from Ollama default
        return AsyncOpenAI(api_key=settings.OPENAI_API_KEY), settings.EMBEDDING_MODEL
    # Default: Ollama local embeddings
    client = AsyncOpenAI(base_url=f"{settings.OLLAMA_BASE_URL}/v1", api_key="ollama")
    return client, settings.OLLAMA_EMBED_MODEL


async def _embed(text_: str) -> list[float]:
    client, model = _get_embed_client()
    response = await client.embeddings.create(model=model, input=text_)
    return response.data[0].embedding


def _invoice_text(invoice: dict) -> str:
    parts = [
        invoice.get("description") or "",
        invoice.get("vendor_name") or "",
        str(invoice.get("total_amount") or ""),
        str(invoice.get("invoice_date") or ""),
        invoice.get("invoice_number") or "",
    ]
    return " | ".join(p for p in parts if p)


async def upsert_invoice_embedding(
    invoice_id: str,
    invoice: dict,
    db: AsyncSession,
) -> LLMEmbedding:
    """Create or update the embedding for a single invoice."""
    content = _invoice_text(invoice)
    chash   = _content_hash(content)

    existing = await db.execute(
        select(LLMEmbedding).where(
            LLMEmbedding.document_type == "invoice",
            LLMEmbedding.document_id   == invoice_id,
        )
    )
    row = existing.scalar_one_or_none()

    if row and row.content_hash == chash:
        return row  # Content unchanged — skip re-embedding

    vector = await _embed(content)

    if row:
        row.content_hash    = chash
        row.embedding       = vector
        row.metadata_       = invoice
        row.embedding_model = settings.EMBEDDING_MODEL
    else:
        row = LLMEmbedding(
            document_type   = "invoice",
            document_id     = invoice_id,
            content_hash    = chash,
            embedding       = vector,
            embedding_model = settings.EMBEDDING_MODEL,
            metadata_       = invoice,
        )
        db.add(row)

    await db.flush()
    return row


async def find_similar_invoices(
    invoice_id: str,
    invoice: dict,
    db: AsyncSession,
    top_k: int = 5,
    threshold: float = 0.12,  # cosine distance — lower = more similar (0 = identical)
) -> list[dict]:
    """Return invoices similar to the given one (excluding itself)."""
    content      = _invoice_text(invoice)
    query_vector = await _embed(content)

    sql = text("""
        SELECT
            document_id,
            metadata,
            embedding <=> CAST(:vec AS vector) AS distance
        FROM mlops.llm_embeddings
        WHERE document_type = 'invoice'
          AND document_id   != :exclude_id
          AND embedding <=> CAST(:vec AS vector) < :threshold
        ORDER BY distance
        LIMIT :top_k
    """)

    result = await db.execute(sql, {
        "vec":        json.dumps(query_vector),
        "exclude_id": invoice_id,
        "threshold":  threshold,
        "top_k":      top_k,
    })
    return [
        {
            "invoice_id": r.document_id,
            "similarity": round(1 - r.distance, 4),
            "distance":   round(r.distance, 4),
            "metadata":   r.metadata,
        }
        for r in result.fetchall()
    ]


async def reindex_all_invoices(db: AsyncSession) -> dict:
    """Embed all invoices (admin operation)."""
    from app.models.ap import Invoice, Vendor
    from sqlalchemy import select as sa_select

    result = await db.execute(
        sa_select(Invoice, Vendor.name.label("vendor_name"))
        .join(Vendor, Invoice.vendor_id == Vendor.id)
    )
    rows = result.fetchall()

    embedded = skipped = errors = 0
    for inv, vendor_name in rows:
        try:
            invoice_dict = {
                "invoice_id":     inv.id,
                "invoice_number": inv.invoice_number,
                "vendor_name":    vendor_name,
                "description":    inv.description,
                "total_amount":   str(inv.total_amount),
                "invoice_date":   str(inv.invoice_date) if inv.invoice_date else None,
            }
            content = _invoice_text(invoice_dict)
            chash   = _content_hash(content)

            existing = await db.execute(
                select(LLMEmbedding).where(
                    LLMEmbedding.document_type == "invoice",
                    LLMEmbedding.document_id   == inv.id,
                    LLMEmbedding.content_hash  == chash,
                )
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue

            await upsert_invoice_embedding(inv.id, invoice_dict, db)
            embedded += 1
        except Exception as exc:
            logger.error(f"Failed to embed invoice {inv.id}: {exc}")
            errors += 1

    return {"embedded": embedded, "skipped": skipped, "errors": errors}
