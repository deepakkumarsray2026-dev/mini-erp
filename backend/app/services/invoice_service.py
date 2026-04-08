"""
invoice_service.py  —  AP: Vendors, Invoices, Vouchers CRUD
"""
from datetime import date
from decimal import Decimal
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.models.ap import Vendor, Invoice, InvoiceLine, Voucher, InvoiceStatus, VendorStatus
from app.schemas.ap import (
    VendorCreate, VendorUpdate,
    InvoiceCreate, InvoiceUpdate, InvoiceApproveRequest,
    VoucherCreate,
)


# ── Vendors ───────────────────────────────────────────────────────────────────

async def list_vendors(
    db: AsyncSession,
    search: str = "",
    page: int = 1,
    page_size: int = 20,
    active_only: bool = True,
) -> tuple[list[Vendor], int]:
    q = select(Vendor)
    if active_only:
        q = q.where(Vendor.is_active == True)
    if search:
        term = f"%{search}%"
        q = q.where(or_(Vendor.name.ilike(term), Vendor.vendor_id.ilike(term), Vendor.email.ilike(term)))
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    result = await db.execute(q.order_by(Vendor.name).offset((page - 1) * page_size).limit(page_size))
    return result.scalars().all(), total


async def get_vendor(db: AsyncSession, vendor_id: str) -> Vendor:
    result = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


async def create_vendor(db: AsyncSession, data: VendorCreate) -> Vendor:
    payload = data.model_dump()
    if not payload.get("vendor_id"):
        count = (await db.execute(select(func.count(Vendor.id)))).scalar() or 0
        payload["vendor_id"] = f"VEN{count + 1:04d}"
    vendor = Vendor(**payload)
    db.add(vendor)
    await db.flush()
    await db.refresh(vendor)
    return vendor


async def update_vendor(db: AsyncSession, vendor_id: str, data: VendorUpdate) -> Vendor:
    vendor = await get_vendor(db, vendor_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(vendor, field, value)
    await db.flush()
    await db.refresh(vendor)
    return vendor


# ── Invoices ──────────────────────────────────────────────────────────────────

async def list_invoices(
    db: AsyncSession,
    vendor_id: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Invoice], int]:
    q = select(Invoice)
    if vendor_id:
        q = q.where(Invoice.vendor_id == vendor_id)
    if status:
        q = q.where(Invoice.status == status)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    result = await db.execute(
        q.order_by(Invoice.created_at.desc())
         .offset((page - 1) * page_size).limit(page_size)
    )
    return result.scalars().all(), total


async def get_invoice(db: AsyncSession, invoice_id: str) -> Invoice:
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id)
        .options(selectinload(Invoice.lines))
    )
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return inv


async def create_invoice(db: AsyncSession, data: InvoiceCreate) -> Invoice:
    lines_data = data.model_dump(exclude={"lines"})
    invoice = Invoice(**lines_data, status=InvoiceStatus.DRAFT)
    db.add(invoice)
    await db.flush()

    for line_data in data.lines:
        line = InvoiceLine(**line_data.model_dump(), invoice_id=invoice.id)
        db.add(line)

    await db.flush()
    await db.refresh(invoice)
    return invoice


async def update_invoice(db: AsyncSession, invoice_id: str, data: InvoiceUpdate) -> Invoice:
    invoice = await get_invoice(db, invoice_id)
    if invoice.status in (InvoiceStatus.PAID, InvoiceStatus.CANCELLED):
        raise HTTPException(status_code=409, detail=f"Cannot update invoice with status '{invoice.status}'")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(invoice, field, value)
    await db.flush()
    await db.refresh(invoice)
    return invoice


async def approve_invoice(db: AsyncSession, invoice_id: str, data: InvoiceApproveRequest) -> Invoice:
    invoice = await get_invoice(db, invoice_id)
    if invoice.status not in (InvoiceStatus.SUBMITTED, InvoiceStatus.UNDER_REVIEW):
        raise HTTPException(status_code=409, detail=f"Cannot approve invoice with status '{invoice.status}'")
    invoice.status = InvoiceStatus.APPROVED
    await db.flush()
    await db.refresh(invoice)
    return invoice


async def submit_invoice(db: AsyncSession, invoice_id: str) -> Invoice:
    invoice = await get_invoice(db, invoice_id)
    if invoice.status != InvoiceStatus.DRAFT:
        raise HTTPException(status_code=409, detail="Only draft invoices can be submitted")
    invoice.status = InvoiceStatus.SUBMITTED
    await db.flush()
    await db.refresh(invoice)
    return invoice


# ── Vouchers ──────────────────────────────────────────────────────────────────

async def list_vouchers(db: AsyncSession, status: str | None = None, page: int = 1, page_size: int = 20) -> tuple[list[Voucher], int]:
    q = select(Voucher)
    if status:
        q = q.where(Voucher.status == status)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    result = await db.execute(q.order_by(Voucher.scheduled_date).offset((page - 1) * page_size).limit(page_size))
    return result.scalars().all(), total


async def get_voucher(db: AsyncSession, voucher_id: str) -> Voucher:
    result = await db.execute(select(Voucher).where(Voucher.id == voucher_id))
    v = result.scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=404, detail="Voucher not found")
    return v


async def create_voucher(db: AsyncSession, data: VoucherCreate, approved_by: str) -> Voucher:
    invoice = await get_invoice(db, data.invoice_id)
    if invoice.status != InvoiceStatus.APPROVED:
        raise HTTPException(status_code=409, detail="Invoice must be approved before creating voucher")
    existing = await db.execute(select(Voucher).where(Voucher.invoice_id == data.invoice_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Voucher already exists for this invoice")

    count = (await db.execute(select(func.count(Voucher.id)))).scalar() or 0
    voucher = Voucher(
        **data.model_dump(),
        voucher_number=f"VCH-{count + 1:05d}",
        currency=invoice.currency,
        approved_by=approved_by,
        status="pending",
    )
    db.add(voucher)
    invoice.status = InvoiceStatus.MATCHED
    await db.flush()
    await db.refresh(voucher)
    return voucher


async def mark_voucher_paid(db: AsyncSession, voucher_id: str, paid_date: date) -> Voucher:
    voucher = await get_voucher(db, voucher_id)
    if voucher.status == "paid":
        raise HTTPException(status_code=409, detail="Voucher already paid")
    voucher.status    = "paid"
    voucher.paid_date = paid_date
    invoice = await get_invoice(db, voucher.invoice_id)
    invoice.status = InvoiceStatus.PAID
    await db.flush()
    await db.refresh(voucher)
    return voucher
