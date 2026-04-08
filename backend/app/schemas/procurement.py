from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel


# ── Purchase Requisition ──────────────────────────────────────────────────────

class PRCreate(BaseModel):
    title: str
    justification: str | None = None
    required_date: date | None = None
    currency: str = "GBP"

class PRUpdate(BaseModel):
    title: str | None = None
    justification: str | None = None
    required_date: date | None = None
    status: str | None = None

class PRResponse(BaseModel):
    id: str
    pr_number: str
    requested_by: str
    department_id: str
    title: str
    justification: str | None = None
    required_date: date | None = None
    total_amount: Decimal
    currency: str
    status: str
    approved_by: str | None = None
    created_at: datetime
    model_config = {"from_attributes": True}


# ── PO Line ───────────────────────────────────────────────────────────────────

class POLineCreate(BaseModel):
    line_number: int
    item_code: str | None = None
    description: str
    quantity: Decimal
    unit_of_measure: str = "EA"
    unit_price: Decimal
    amount: Decimal
    gl_account_code: str | None = None

class POLineResponse(POLineCreate):
    id: str
    po_id: str
    received_quantity: Decimal
    model_config = {"from_attributes": True}


# ── Purchase Order ────────────────────────────────────────────────────────────

class POCreate(BaseModel):
    requisition_id: str | None = None
    vendor_id: str
    issued_date: date
    expected_delivery: date | None = None
    total_amount: Decimal
    currency: str = "GBP"
    terms: str | None = None
    lines: list[POLineCreate] = []

class POUpdate(BaseModel):
    expected_delivery: date | None = None
    status: str | None = None
    terms: str | None = None

class POResponse(BaseModel):
    id: str
    po_number: str
    requisition_id: str | None = None
    vendor_id: str
    issued_date: date
    expected_delivery: date | None = None
    total_amount: Decimal
    currency: str
    status: str
    approved_by: str | None = None
    lines: list[POLineResponse] = []
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Goods Receipt ─────────────────────────────────────────────────────────────

class GoodsReceiptCreate(BaseModel):
    po_id: str
    receipt_date: date
    notes: str | None = None

class GoodsReceiptResponse(GoodsReceiptCreate):
    id: str
    receipt_number: str
    received_by: str
    created_at: datetime
    model_config = {"from_attributes": True}
