"""
Accounts Payable API  —  Vendors, Invoices, Vouchers
"""
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import can_read, can_create, can_update, can_approve, ModuleName
from app.schemas.ap import (
    VendorCreate, VendorUpdate, VendorResponse,
    InvoiceCreate, InvoiceUpdate, InvoiceResponse, InvoiceApproveRequest,
    VoucherCreate, VoucherResponse,
)
from app.schemas.common import PaginatedResponse, MessageResponse, paginate
from app.services import invoice_service

router = APIRouter()


# ── Vendors ───────────────────────────────────────────────────────────────────

@router.get("/vendors", response_model=PaginatedResponse[VendorResponse])
async def list_vendors(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = "",
    active_only: bool = True,
    _=Depends(can_read(ModuleName.AP)),
    db: AsyncSession = Depends(get_db),
):
    vendors, total = await invoice_service.list_vendors(db, search, page, page_size, active_only)
    return paginate(vendors, total, page, page_size)


@router.post("/vendors", response_model=VendorResponse, status_code=201)
async def create_vendor(
    data: VendorCreate,
    _=Depends(can_create(ModuleName.AP)),
    db: AsyncSession = Depends(get_db),
):
    return await invoice_service.create_vendor(db, data)


@router.get("/vendors/{vendor_id}", response_model=VendorResponse)
async def get_vendor(
    vendor_id: str,
    _=Depends(can_read(ModuleName.AP)),
    db: AsyncSession = Depends(get_db),
):
    return await invoice_service.get_vendor(db, vendor_id)


@router.patch("/vendors/{vendor_id}", response_model=VendorResponse)
async def update_vendor(
    vendor_id: str,
    data: VendorUpdate,
    _=Depends(can_update(ModuleName.AP)),
    db: AsyncSession = Depends(get_db),
):
    return await invoice_service.update_vendor(db, vendor_id, data)


# ── Invoices ──────────────────────────────────────────────────────────────────

@router.get("/invoices", response_model=PaginatedResponse[InvoiceResponse])
async def list_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    vendor_id: str | None = None,
    status: str | None = None,
    _=Depends(can_read(ModuleName.AP)),
    db: AsyncSession = Depends(get_db),
):
    invoices, total = await invoice_service.list_invoices(db, vendor_id, status, page, page_size)
    return paginate(invoices, total, page, page_size)


@router.post("/invoices", response_model=InvoiceResponse, status_code=201)
async def create_invoice(
    data: InvoiceCreate,
    _=Depends(can_create(ModuleName.AP)),
    db: AsyncSession = Depends(get_db),
):
    return await invoice_service.create_invoice(db, data)


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: str,
    _=Depends(can_read(ModuleName.AP)),
    db: AsyncSession = Depends(get_db),
):
    return await invoice_service.get_invoice(db, invoice_id)


@router.patch("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: str,
    data: InvoiceUpdate,
    _=Depends(can_update(ModuleName.AP)),
    db: AsyncSession = Depends(get_db),
):
    return await invoice_service.update_invoice(db, invoice_id, data)


@router.post("/invoices/{invoice_id}/submit", response_model=InvoiceResponse)
async def submit_invoice(
    invoice_id: str,
    _=Depends(can_update(ModuleName.AP)),
    db: AsyncSession = Depends(get_db),
):
    return await invoice_service.submit_invoice(db, invoice_id)


@router.post("/invoices/{invoice_id}/approve", response_model=InvoiceResponse)
async def approve_invoice(
    invoice_id: str,
    data: InvoiceApproveRequest,
    _=Depends(can_approve(ModuleName.AP)),
    db: AsyncSession = Depends(get_db),
):
    return await invoice_service.approve_invoice(db, invoice_id, data)


# ── Vouchers ──────────────────────────────────────────────────────────────────

@router.get("/vouchers", response_model=PaginatedResponse[VoucherResponse])
async def list_vouchers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    _=Depends(can_read(ModuleName.AP)),
    db: AsyncSession = Depends(get_db),
):
    vouchers, total = await invoice_service.list_vouchers(db, status, page, page_size)
    return paginate(vouchers, total, page, page_size)


@router.post("/vouchers", response_model=VoucherResponse, status_code=201)
async def create_voucher(
    data: VoucherCreate,
    ctx=Depends(can_approve(ModuleName.AP)),
    db: AsyncSession = Depends(get_db),
):
    return await invoice_service.create_voucher(db, data, approved_by=ctx.user.id)


@router.get("/vouchers/{voucher_id}", response_model=VoucherResponse)
async def get_voucher(
    voucher_id: str,
    _=Depends(can_read(ModuleName.AP)),
    db: AsyncSession = Depends(get_db),
):
    return await invoice_service.get_voucher(db, voucher_id)


@router.post("/vouchers/{voucher_id}/pay", response_model=VoucherResponse)
async def mark_voucher_paid(
    voucher_id: str,
    paid_date: date,
    _=Depends(can_update(ModuleName.AP)),
    db: AsyncSession = Depends(get_db),
):
    return await invoice_service.mark_voucher_paid(db, voucher_id, paid_date)
