"""
Invoice OCR service — uses Claude Vision to extract structured data from invoice images/PDFs.

Supported formats: JPEG, PNG, GIF, WebP (Claude Vision native).
PDF pages are extracted as images before sending.

Returns a structured dict with extracted invoice fields.
"""
import base64
import os
import time
from pathlib import Path

import anthropic
from loguru import logger

from app.core.config import settings

_EXTRACTION_PROMPT = """
Extract all invoice data from this image and return a JSON object with these fields
(use null for any field not visible):

{
  "invoice_number":   "string or null",
  "vendor_name":      "string or null",
  "vendor_address":   "string or null",
  "vendor_email":     "string or null",
  "invoice_date":     "YYYY-MM-DD or null",
  "due_date":         "YYYY-MM-DD or null",
  "currency":         "3-letter ISO code e.g. USD, GBP, EUR or null",
  "subtotal":         number or null,
  "tax_amount":       number or null,
  "tax_rate":         number or null (percentage, e.g. 20 for 20%),
  "total_amount":     number or null,
  "payment_terms":    "e.g. Net 30 or null",
  "description":      "brief description of goods/services or null",
  "line_items": [
    {
      "description": "string",
      "quantity":    number or null,
      "unit_price":  number or null,
      "amount":      number
    }
  ],
  "notes": "any other relevant information or null"
}

Return ONLY the JSON object. No markdown, no explanation.
"""

_MEDIA_TYPES = {
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png":  "image/png",
    ".gif":  "image/gif",
    ".webp": "image/webp",
}


def _read_image_as_base64(file_path: str) -> tuple[str, str]:
    """Returns (base64_data, media_type). Raises for unsupported types."""
    suffix = Path(file_path).suffix.lower()
    media_type = _MEDIA_TYPES.get(suffix)
    if not media_type:
        raise ValueError(f"Unsupported file type: {suffix}. Supported: {list(_MEDIA_TYPES)}")
    with open(file_path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    return data, media_type


async def extract_invoice(file_path: str) -> dict:
    """
    Run Claude Vision OCR on an invoice file.

    Returns:
        {
          "extracted_data": {...},   # structured invoice fields
          "model_used": str,
          "input_tokens": int,
          "output_tokens": int,
          "latency_ms": int,
        }
    """
    import json

    start = time.time()
    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    image_data, media_type = _read_image_as_base64(file_path)

    response = await client.messages.create(
        model=settings.CHAT_MODEL,
        max_tokens=1500,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type":       "base64",
                            "media_type": media_type,
                            "data":       image_data,
                        },
                    },
                    {"type": "text", "text": _EXTRACTION_PROMPT},
                ],
            }
        ],
    )

    raw_text = next((b.text for b in response.content if hasattr(b, "text")), "{}")

    # Strip markdown code fences if present
    if raw_text.strip().startswith("```"):
        raw_text = raw_text.strip().strip("`").lstrip("json").strip()

    try:
        extracted = json.loads(raw_text)
    except json.JSONDecodeError:
        logger.warning(f"OCR JSON parse failed, raw={raw_text[:200]}")
        extracted = {"raw_text": raw_text, "parse_error": True}

    latency_ms = int((time.time() - start) * 1000)
    return {
        "extracted_data": extracted,
        "model_used":     settings.CHAT_MODEL,
        "input_tokens":   response.usage.input_tokens,
        "output_tokens":  response.usage.output_tokens,
        "latency_ms":     latency_ms,
    }
