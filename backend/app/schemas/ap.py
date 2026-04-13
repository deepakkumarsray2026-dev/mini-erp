from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, EmailStr


# ── Vendor ────────────────────────────────────────────────────────────────────

class VendorBase(BaseModel):
    name: str
    legal_name: str | None = None
    tax_id: str | None = None
    vat_number: str | None = None
    email: str | None = None
    phone: str | None = None
    address_line1: str | None = None
    city: str | None = None
    country: str = "GB"
    payment_terms_days: int = 30
    bank_account: str | None = None
    bank_sort_code: str | None = None

class VendorCreate(VendorBase):
    vendor_id: str | None = None

class VendorUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    address_line1: str | None = None
    city: str | None = None
    payment_terms_days: int | None = None
    bank_account: str | None = None
    bank_sort_code: str | None = None
    status: str | None = None

class VendorResponse(VendorBase):
    id: str
    vendor_id: str
    status: str
    risk_score: float | None = None
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Invoice Line ──────────────────────────────────────────────────────────────

class InvoiceLineCreate(BaseModel):
    line_number: int
    description: str
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal
    tax_rate: Decimal = Decimal("0")
    gl_account_code: str | None = None

class InvoiceLineResponse(InvoiceLineCreate):
    id: str
    invoice_id: str
    model_config = {"from_attributes": True}


# ── Invoice ───────────────────────────────────────────────────────────────────

class InvoiceCreate(BaseModel):
    invoice_number: str
    vendor_id: str
    po_id: str | None = None
    invoice_date: date
    due_date: date
    currency: str = "GBP"
    subtotal: Decimal
    tax_amount: Decimal = Decimal("0")
    total_amount: Decimal
    description: str | None = None
    lines: list[InvoiceLineCreate] = []

class InvoiceUpdate(BaseModel):
    due_date: date | None = None
    description: str | None = None
    status: str | None = None

class InvoiceResponse(BaseModel):
    id: str
    invoice_number: str
    vendor_id: str
    vendor_name: str | None = None
    po_id: str | None = None
    invoice_date: date
    due_date: date
    currency: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal | None = None
    status: str
    description: str | None = None
    category: str | None = None
    is_duplicate: bool
    lines: list[InvoiceLineResponse] = []
    created_at: datetime
    model_config = {"from_attributes": True}

class InvoiceApproveRequest(BaseModel):
    approved_by: str


# ── Voucher ───────────────────────────────────────────────────────────────────

class VoucherCreate(BaseModel):
    invoice_id: str
    amount: Decimal
    payment_method: str = "bank_transfer"
    scheduled_date: date

class VoucherResponse(BaseModel):
    id: str
    voucher_number: str
    invoice_id: str
    amount: Decimal
    currency: str
    payment_method: str
    scheduled_date: date
    paid_date: date | None = None
    status: str
    approved_by: str | None = None
    created_at: datetime
    model_config = {"from_attributes": True}
