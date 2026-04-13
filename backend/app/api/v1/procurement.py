"""
Procurement API  —  Purchase Requisitions, Purchase Orders, Goods Receipts
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import (
    can_read, can_create, can_update, can_approve,
    ModuleName, get_current_user,
)
from app.schemas.procurement import (
    PRCreate, PRUpdate, PRResponse,
    POCreate, POUpdate, POResponse,
    GoodsReceiptCreate, GoodsReceiptResponse,
)
from app.schemas.common import PaginatedResponse, MessageResponse, paginate
from app.services import procurement_service

router = APIRouter()


# ── Purchase Requisitions ─────────────────────────────────────────────────────

@router.get("/requisitions", response_model=PaginatedResponse[PRResponse])
async def list_prs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    employee_id: str | None = None,
    status: str | None = None,
    _=Depends(can_read(ModuleName.PROCUREMENT)),
    db: AsyncSession = Depends(get_db),
):
    prs, total = await procurement_service.list_prs(db, employee_id, status, page, page_size)
    items = [
        {
            "id":             pr.id,
            "pr_number":      pr.pr_number,
            "requested_by":   pr.requested_by,
            "requester_name": f"{pr.requester.first_name} {pr.requester.last_name}" if pr.requester else None,
            "department_id":  pr.department_id,
            "title":          pr.title,
            "justification":  pr.justification,
            "required_date":  pr.required_date,
            "total_amount":   pr.total_amount,
            "currency":       pr.currency,
            "status":         pr.status,
            "approved_by":    pr.approved_by,
            "created_at":     pr.created_at,
        }
        for pr in prs
    ]
    return paginate(items, total, page, page_size)


@router.post("/requisitions", response_model=PRResponse, status_code=201)
async def create_pr(
    data: PRCreate,
    ctx=Depends(can_create(ModuleName.PROCUREMENT)),
    db: AsyncSession = Depends(get_db),
):
    from app.models.auth import User
    from app.models.hcm import Employee
    from sqlalchemy import select
    user_result = await db.execute(select(User).where(User.id == ctx.user.id))
    user = user_result.scalar_one_or_none()
    employee_id = user.employee_id if user and user.employee_id else ctx.user.id

    # get department_id from employee
    emp_result = await db.execute(select(Employee).where(Employee.id == employee_id))
    emp = emp_result.scalar_one_or_none()
    department_id = emp.department_id if emp else ""

    return await procurement_service.create_pr(db, data, employee_id, department_id)


@router.get("/requisitions/{pr_id}", response_model=PRResponse)
async def get_pr(
    pr_id: str,
    _=Depends(can_read(ModuleName.PROCUREMENT)),
    db: AsyncSession = Depends(get_db),
):
    return await procurement_service.get_pr(db, pr_id)


@router.patch("/requisitions/{pr_id}", response_model=PRResponse)
async def update_pr(
    pr_id: str,
    data: PRUpdate,
    _=Depends(can_update(ModuleName.PROCUREMENT)),
    db: AsyncSession = Depends(get_db),
):
    return await procurement_service.update_pr(db, pr_id, data)


@router.post("/requisitions/{pr_id}/submit", response_model=PRResponse)
async def submit_pr(
    pr_id: str,
    _=Depends(can_update(ModuleName.PROCUREMENT)),
    db: AsyncSession = Depends(get_db),
):
    return await procurement_service.submit_pr(db, pr_id)


@router.post("/requisitions/{pr_id}/approve", response_model=PRResponse)
async def approve_pr(
    pr_id: str,
    ctx=Depends(can_approve(ModuleName.PROCUREMENT)),
    db: AsyncSession = Depends(get_db),
):
    return await procurement_service.approve_pr(db, pr_id, approved_by=ctx.user.id)


# ── Purchase Orders ───────────────────────────────────────────────────────────

@router.get("/orders", response_model=PaginatedResponse[POResponse])
async def list_pos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    vendor_id: str | None = None,
    status: str | None = None,
    _=Depends(can_read(ModuleName.PROCUREMENT)),
    db: AsyncSession = Depends(get_db),
):
    pos, total = await procurement_service.list_pos(db, vendor_id, status, page, page_size)
    items = [
        {
            "id":                po.id,
            "po_number":         po.po_number,
            "requisition_id":    po.requisition_id,
            "vendor_id":         po.vendor_id,
            "vendor_name":       po.vendor.name if po.vendor else None,
            "issued_date":       po.issued_date,
            "expected_delivery": po.expected_delivery,
            "total_amount":      po.total_amount,
            "currency":          po.currency,
            "status":            po.status,
            "approved_by":       po.approved_by,
            "lines":             po.lines,
            "created_at":        po.created_at,
        }
        for po in pos
    ]
    return paginate(items, total, page, page_size)


@router.post("/orders", response_model=POResponse, status_code=201)
async def create_po(
    data: POCreate,
    ctx=Depends(can_create(ModuleName.PROCUREMENT)),
    db: AsyncSession = Depends(get_db),
):
    return await procurement_service.create_po(db, data, approved_by=ctx.user.id)


@router.get("/orders/{po_id}", response_model=POResponse)
async def get_po(
    po_id: str,
    _=Depends(can_read(ModuleName.PROCUREMENT)),
    db: AsyncSession = Depends(get_db),
):
    return await procurement_service.get_po(db, po_id)


@router.patch("/orders/{po_id}", response_model=POResponse)
async def update_po(
    po_id: str,
    data: POUpdate,
    _=Depends(can_update(ModuleName.PROCUREMENT)),
    db: AsyncSession = Depends(get_db),
):
    return await procurement_service.update_po(db, po_id, data)


@router.post("/orders/{po_id}/issue", response_model=POResponse)
async def issue_po(
    po_id: str,
    _=Depends(can_approve(ModuleName.PROCUREMENT)),
    db: AsyncSession = Depends(get_db),
):
    return await procurement_service.issue_po(db, po_id)


# ── Goods Receipts ────────────────────────────────────────────────────────────

@router.get("/receipts", response_model=list[GoodsReceiptResponse])
async def list_receipts(
    po_id: str | None = None,
    _=Depends(can_read(ModuleName.PROCUREMENT)),
    db: AsyncSession = Depends(get_db),
):
    return await procurement_service.list_receipts(db, po_id)


@router.post("/receipts", response_model=GoodsReceiptResponse, status_code=201)
async def create_receipt(
    data: GoodsReceiptCreate,
    ctx=Depends(can_create(ModuleName.PROCUREMENT)),
    db: AsyncSession = Depends(get_db),
):
    from app.models.auth import User
    from sqlalchemy import select
    user_result = await db.execute(select(User).where(User.id == ctx.user.id))
    user = user_result.scalar_one_or_none()
    received_by = user.employee_id if user and user.employee_id else ctx.user.id
    return await procurement_service.create_receipt(db, data, received_by=received_by)
