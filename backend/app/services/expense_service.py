"""
expense_service.py  —  Expense reports & categories CRUD
"""
from decimal import Decimal
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.models.expenses import ExpenseReport, ExpenseLine, ExpenseCategory, ExpenseStatus
from app.schemas.expenses import (
    ExpenseCategoryCreate, ExpenseReportCreate, ExpenseReportUpdate,
    ExpenseApproveRequest, ExpenseRejectRequest,
)


# ── Categories ────────────────────────────────────────────────────────────────

async def list_categories(db: AsyncSession) -> list[ExpenseCategory]:
    result = await db.execute(select(ExpenseCategory).where(ExpenseCategory.is_active == True))
    return result.scalars().all()


async def create_category(db: AsyncSession, data: ExpenseCategoryCreate) -> ExpenseCategory:
    existing = await db.execute(select(ExpenseCategory).where(ExpenseCategory.code == data.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Category code '{data.code}' already exists")
    cat = ExpenseCategory(**data.model_dump())
    db.add(cat)
    await db.flush()
    await db.refresh(cat)
    return cat


# ── Expense Reports ───────────────────────────────────────────────────────────

async def list_reports(
    db: AsyncSession,
    employee_id: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[ExpenseReport], int]:
    q = select(ExpenseReport)
    if employee_id:
        q = q.where(ExpenseReport.employee_id == employee_id)
    if status:
        q = q.where(ExpenseReport.status == status)
    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar()
    result = await db.execute(
        q.order_by(ExpenseReport.created_at.desc())
         .offset((page - 1) * page_size).limit(page_size)
    )
    return result.scalars().all(), total


async def get_report(db: AsyncSession, report_id: str) -> ExpenseReport:
    result = await db.execute(
        select(ExpenseReport)
        .where(ExpenseReport.id == report_id)
        .options(selectinload(ExpenseReport.lines))
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Expense report not found")
    return report


async def create_report(db: AsyncSession, data: ExpenseReportCreate, employee_id: str) -> ExpenseReport:
    count_res = await db.execute(select(func.count(ExpenseReport.id)))
    count = count_res.scalar() or 0
    report_number = f"EXP-{count + 1:05d}"

    lines_data = data.model_dump(exclude={"lines"})
    report = ExpenseReport(
        **lines_data,
        report_number=report_number,
        employee_id=employee_id,
        status=ExpenseStatus.DRAFT,
    )
    db.add(report)
    await db.flush()

    total = Decimal("0")
    for line_data in data.lines:
        line = ExpenseLine(**line_data.model_dump(), report_id=report.id)
        db.add(line)
        total += line_data.amount

    report.total_amount = total
    await db.flush()
    await db.refresh(report)
    return report


async def submit_report(db: AsyncSession, report_id: str, employee_id: str) -> ExpenseReport:
    report = await get_report(db, report_id)
    if report.employee_id != employee_id:
        raise HTTPException(status_code=403, detail="Not your expense report")
    if report.status != ExpenseStatus.DRAFT:
        raise HTTPException(status_code=409, detail=f"Cannot submit report with status '{report.status}'")
    report.status = ExpenseStatus.SUBMITTED
    await db.flush()
    await db.refresh(report)
    return report


async def approve_report(db: AsyncSession, report_id: str, data: ExpenseApproveRequest) -> ExpenseReport:
    report = await get_report(db, report_id)
    if report.status not in (ExpenseStatus.SUBMITTED, ExpenseStatus.UNDER_REVIEW):
        raise HTTPException(status_code=409, detail=f"Cannot approve report with status '{report.status}'")
    report.status      = ExpenseStatus.APPROVED
    report.approved_by = data.approved_by
    await db.flush()
    await db.refresh(report)
    return report


async def reject_report(db: AsyncSession, report_id: str, data: ExpenseRejectRequest) -> ExpenseReport:
    report = await get_report(db, report_id)
    if report.status not in (ExpenseStatus.SUBMITTED, ExpenseStatus.UNDER_REVIEW):
        raise HTTPException(status_code=409, detail=f"Cannot reject report with status '{report.status}'")
    report.status           = ExpenseStatus.REJECTED
    report.rejection_reason = data.reason
    await db.flush()
    await db.refresh(report)
    return report


async def delete_report(db: AsyncSession, report_id: str, employee_id: str) -> None:
    report = await get_report(db, report_id)
    if report.employee_id != employee_id:
        raise HTTPException(status_code=403, detail="Not your expense report")
    if report.status != ExpenseStatus.DRAFT:
        raise HTTPException(status_code=409, detail="Only draft reports can be deleted")
    await db.delete(report)
