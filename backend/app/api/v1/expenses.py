"""
Expenses API  —  Categories, Reports, Lines
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import (
    can_read, can_create, can_update, can_delete, can_approve,
    ModuleName, get_current_user,
)
from app.schemas.expenses import (
    ExpenseCategoryCreate, ExpenseCategoryResponse,
    ExpenseReportCreate, ExpenseReportUpdate,
    ExpenseReportResponse, ExpenseReportListResponse,
    ExpenseApproveRequest, ExpenseRejectRequest,
)
from app.schemas.common import PaginatedResponse, MessageResponse, paginate
from app.services import expense_service

router = APIRouter()


# ── Categories ────────────────────────────────────────────────────────────────

@router.get("/categories", response_model=list[ExpenseCategoryResponse])
async def list_categories(
    _=Depends(can_read(ModuleName.EXPENSES)),
    db: AsyncSession = Depends(get_db),
):
    return await expense_service.list_categories(db)


@router.post("/categories", response_model=ExpenseCategoryResponse, status_code=201)
async def create_category(
    data: ExpenseCategoryCreate,
    _=Depends(can_create(ModuleName.EXPENSES)),
    db: AsyncSession = Depends(get_db),
):
    return await expense_service.create_category(db, data)


# ── Expense Reports ───────────────────────────────────────────────────────────

@router.get("/reports", response_model=PaginatedResponse[ExpenseReportListResponse])
async def list_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    employee_id: str | None = None,
    status: str | None = None,
    _=Depends(can_read(ModuleName.EXPENSES)),
    db: AsyncSession = Depends(get_db),
):
    reports, total = await expense_service.list_reports(db, employee_id, status, page, page_size)
    items = [
        {
            "id":            r.id,
            "report_number": r.report_number,
            "employee_id":   r.employee_id,
            "employee_name": f"{r.employee.first_name} {r.employee.last_name}" if r.employee else None,
            "title":         r.title,
            "period_start":  r.period_start,
            "period_end":    r.period_end,
            "total_amount":  r.total_amount,
            "currency":      r.currency,
            "status":        r.status,
            "is_flagged":    r.is_flagged,
            "created_at":    r.created_at,
        }
        for r in reports
    ]
    return paginate(items, total, page, page_size)


@router.post("/reports", response_model=ExpenseReportResponse, status_code=201)
async def create_report(
    data: ExpenseReportCreate,
    ctx=Depends(can_create(ModuleName.EXPENSES)),
    db: AsyncSession = Depends(get_db),
):
    # Resolve the employee_id from the user's linked employee record
    from app.models.auth import User
    from sqlalchemy import select
    result = await db.execute(
        select(User).where(User.id == ctx.user.id)
    )
    user = result.scalar_one_or_none()
    employee_id = user.employee_id if user and user.employee_id else ctx.user.id
    return await expense_service.create_report(db, data, employee_id=employee_id)


@router.get("/reports/{report_id}", response_model=ExpenseReportResponse)
async def get_report(
    report_id: str,
    _=Depends(can_read(ModuleName.EXPENSES)),
    db: AsyncSession = Depends(get_db),
):
    return await expense_service.get_report(db, report_id)


@router.post("/reports/{report_id}/submit", response_model=ExpenseReportResponse)
async def submit_report(
    report_id: str,
    ctx=Depends(can_update(ModuleName.EXPENSES)),
    db: AsyncSession = Depends(get_db),
):
    from app.models.auth import User
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == ctx.user.id))
    user = result.scalar_one_or_none()
    employee_id = user.employee_id if user and user.employee_id else ctx.user.id
    return await expense_service.submit_report(db, report_id, employee_id=employee_id)


@router.post("/reports/{report_id}/approve", response_model=ExpenseReportResponse)
async def approve_report(
    report_id: str,
    data: ExpenseApproveRequest,
    _=Depends(can_approve(ModuleName.EXPENSES)),
    db: AsyncSession = Depends(get_db),
):
    return await expense_service.approve_report(db, report_id, data)


@router.post("/reports/{report_id}/reject", response_model=ExpenseReportResponse)
async def reject_report(
    report_id: str,
    data: ExpenseRejectRequest,
    _=Depends(can_approve(ModuleName.EXPENSES)),
    db: AsyncSession = Depends(get_db),
):
    return await expense_service.reject_report(db, report_id, data)


@router.delete("/reports/{report_id}", response_model=MessageResponse)
async def delete_report(
    report_id: str,
    ctx=Depends(can_delete(ModuleName.EXPENSES)),
    db: AsyncSession = Depends(get_db),
):
    from app.models.auth import User
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == ctx.user.id))
    user = result.scalar_one_or_none()
    employee_id = user.employee_id if user and user.employee_id else ctx.user.id
    await expense_service.delete_report(db, report_id, employee_id=employee_id)
    return {"message": "Expense report deleted"}
