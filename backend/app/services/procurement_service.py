"""
procurement_service.py  —  PR, PO, Goods Receipt CRUD
"""
from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.models.procurement import PurchaseRequisition, PurchaseOrder, POLine, GoodsReceipt
from app.schemas.procurement import PRCreate, PRUpdate, POCreate, POUpdate, GoodsReceiptCreate


# ── Purchase Requisitions ─────────────────────────────────────────────────────

async def list_prs(db: AsyncSession, employee_id: str | None = None, status: str | None = None,
                   page: int = 1, page_size: int = 20) -> tuple[list[PurchaseRequisition], int]:
    q = select(PurchaseRequisition)
    if employee_id:
        q = q.where(PurchaseRequisition.requested_by == employee_id)
    if status:
        q = q.where(PurchaseRequisition.status == status)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    result = await db.execute(q.order_by(PurchaseRequisition.created_at.desc())
                               .offset((page - 1) * page_size).limit(page_size))
    return result.scalars().all(), total


async def get_pr(db: AsyncSession, pr_id: str) -> PurchaseRequisition:
    result = await db.execute(select(PurchaseRequisition).where(PurchaseRequisition.id == pr_id))
    pr = result.scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=404, detail="Purchase requisition not found")
    return pr


async def create_pr(db: AsyncSession, data: PRCreate, employee_id: str, department_id: str) -> PurchaseRequisition:
    count = (await db.execute(select(func.count(PurchaseRequisition.id)))).scalar() or 0
    pr = PurchaseRequisition(
        **data.model_dump(),
        pr_number=f"PR-{count + 1:05d}",
        requested_by=employee_id,
        department_id=department_id,
        status="draft",
    )
    db.add(pr)
    await db.flush()
    await db.refresh(pr)
    return pr


async def update_pr(db: AsyncSession, pr_id: str, data: PRUpdate) -> PurchaseRequisition:
    pr = await get_pr(db, pr_id)
    if pr.status not in ("draft", "submitted"):
        raise HTTPException(status_code=409, detail=f"Cannot update PR with status '{pr.status}'")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(pr, field, value)
    await db.flush()
    await db.refresh(pr)
    return pr


async def submit_pr(db: AsyncSession, pr_id: str) -> PurchaseRequisition:
    pr = await get_pr(db, pr_id)
    if pr.status != "draft":
        raise HTTPException(status_code=409, detail="Only draft PRs can be submitted")
    pr.status = "submitted"
    await db.flush()
    await db.refresh(pr)
    return pr


async def approve_pr(db: AsyncSession, pr_id: str, approved_by: str) -> PurchaseRequisition:
    pr = await get_pr(db, pr_id)
    if pr.status != "submitted":
        raise HTTPException(status_code=409, detail="Only submitted PRs can be approved")
    pr.status      = "approved"
    pr.approved_by = approved_by
    await db.flush()
    await db.refresh(pr)
    return pr


# ── Purchase Orders ───────────────────────────────────────────────────────────

async def list_pos(db: AsyncSession, vendor_id: str | None = None, status: str | None = None,
                   page: int = 1, page_size: int = 20) -> tuple[list[PurchaseOrder], int]:
    q = select(PurchaseOrder)
    if vendor_id:
        q = q.where(PurchaseOrder.vendor_id == vendor_id)
    if status:
        q = q.where(PurchaseOrder.status == status)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    result = await db.execute(q.order_by(PurchaseOrder.created_at.desc())
                               .offset((page - 1) * page_size).limit(page_size))
    return result.scalars().all(), total


async def get_po(db: AsyncSession, po_id: str) -> PurchaseOrder:
    result = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.id == po_id)
        .options(selectinload(PurchaseOrder.lines))
    )
    po = result.scalar_one_or_none()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return po


async def create_po(db: AsyncSession, data: POCreate, approved_by: str) -> PurchaseOrder:
    count = (await db.execute(select(func.count(PurchaseOrder.id)))).scalar() or 0
    lines_data = data.model_dump(exclude={"lines"})
    po = PurchaseOrder(
        **lines_data,
        po_number=f"PO-{count + 1:05d}",
        approved_by=approved_by,
        status="draft",
    )
    db.add(po)
    await db.flush()

    for line_data in data.lines:
        line = POLine(**line_data.model_dump(), po_id=po.id)
        db.add(line)

    await db.flush()
    await db.refresh(po)
    return po


async def update_po(db: AsyncSession, po_id: str, data: POUpdate) -> PurchaseOrder:
    po = await get_po(db, po_id)
    if po.status in ("closed", "cancelled"):
        raise HTTPException(status_code=409, detail=f"Cannot update PO with status '{po.status}'")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(po, field, value)
    await db.flush()
    await db.refresh(po)
    return po


async def issue_po(db: AsyncSession, po_id: str) -> PurchaseOrder:
    po = await get_po(db, po_id)
    if po.status != "draft":
        raise HTTPException(status_code=409, detail="Only draft POs can be issued")
    po.status = "issued"
    await db.flush()
    await db.refresh(po)
    return po


# ── Goods Receipts ────────────────────────────────────────────────────────────

async def list_receipts(db: AsyncSession, po_id: str | None = None) -> list[GoodsReceipt]:
    q = select(GoodsReceipt)
    if po_id:
        q = q.where(GoodsReceipt.po_id == po_id)
    result = await db.execute(q.order_by(GoodsReceipt.receipt_date.desc()))
    return result.scalars().all()


async def create_receipt(db: AsyncSession, data: GoodsReceiptCreate, received_by: str) -> GoodsReceipt:
    po = await get_po(db, data.po_id)
    if po.status not in ("issued", "partial"):
        raise HTTPException(status_code=409, detail="PO must be issued before receiving goods")
    count = (await db.execute(select(func.count(GoodsReceipt.id)))).scalar() or 0
    receipt = GoodsReceipt(
        **data.model_dump(),
        receipt_number=f"GR-{count + 1:05d}",
        received_by=received_by,
    )
    db.add(receipt)
    po.status = "partial"
    await db.flush()
    await db.refresh(receipt)
    return receipt
