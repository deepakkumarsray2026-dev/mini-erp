"""
Payroll API  —  Pay Groups, Periods, Runs, Payslips, Components
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import can_read, can_create, can_update, ModuleName, get_current_user
from app.schemas.payroll import (
    PayGroupCreate, PayGroupResponse,
    PayPeriodResponse,
    PayrollRunCreate, PayrollRunResponse,
    PaySlipResponse,
    PayComponentCreate, PayComponentResponse,
)
from app.schemas.common import PaginatedResponse, MessageResponse, paginate
from app.services import payroll_service

router = APIRouter()


# ── Pay Groups ────────────────────────────────────────────────────────────────

@router.get("/pay-groups", response_model=list[PayGroupResponse])
async def list_pay_groups(
    _=Depends(can_read(ModuleName.PAYROLL)),
    db: AsyncSession = Depends(get_db),
):
    return await payroll_service.list_pay_groups(db)


@router.post("/pay-groups", response_model=PayGroupResponse, status_code=201)
async def create_pay_group(
    data: PayGroupCreate,
    _=Depends(can_create(ModuleName.PAYROLL)),
    db: AsyncSession = Depends(get_db),
):
    return await payroll_service.create_pay_group(db, data)


# ── Pay Periods ───────────────────────────────────────────────────────────────

@router.get("/pay-periods", response_model=PaginatedResponse[PayPeriodResponse])
async def list_pay_periods(
    pay_group_id: str | None = None,
    fiscal_year: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _=Depends(can_read(ModuleName.PAYROLL)),
    db: AsyncSession = Depends(get_db),
):
    periods, total = await payroll_service.list_pay_periods(db, pay_group_id, fiscal_year, page, page_size)
    items = [
        {
            "id":            p.id,
            "pay_group_id":  p.pay_group_id,
            "period_name":   f"FY{p.fiscal_year}-P{p.period_number:02d}",
            "pay_group_name": p.pay_group.name if p.pay_group else None,
            "period_number": p.period_number,
            "fiscal_year":   p.fiscal_year,
            "start_date":    p.start_date,
            "end_date":      p.end_date,
            "pay_date":      p.pay_date,
            "status":        p.status,
        }
        for p in periods
    ]
    return paginate(items, total, page, page_size)


@router.get("/pay-periods/{period_id}", response_model=PayPeriodResponse)
async def get_pay_period(
    period_id: str,
    _=Depends(can_read(ModuleName.PAYROLL)),
    db: AsyncSession = Depends(get_db),
):
    return await payroll_service.get_pay_period(db, period_id)


# ── Payroll Runs ──────────────────────────────────────────────────────────────

@router.get("/runs", response_model=list[PayrollRunResponse])
async def list_payroll_runs(
    pay_period_id: str | None = None,
    _=Depends(can_read(ModuleName.PAYROLL)),
    db: AsyncSession = Depends(get_db),
):
    return await payroll_service.list_payroll_runs(db, pay_period_id)


@router.post("/runs", response_model=PayrollRunResponse, status_code=201)
async def create_payroll_run(
    data: PayrollRunCreate,
    current_user=Depends(can_create(ModuleName.PAYROLL)),
    db: AsyncSession = Depends(get_db),
):
    return await payroll_service.create_payroll_run(db, data, run_by=current_user.user.id)


@router.get("/runs/{run_id}", response_model=PayrollRunResponse)
async def get_payroll_run(
    run_id: str,
    _=Depends(can_read(ModuleName.PAYROLL)),
    db: AsyncSession = Depends(get_db),
):
    return await payroll_service.get_payroll_run(db, run_id)


@router.post("/runs/{run_id}/confirm", response_model=PayrollRunResponse)
async def confirm_payroll_run(
    run_id: str,
    _=Depends(can_update(ModuleName.PAYROLL)),
    db: AsyncSession = Depends(get_db),
):
    return await payroll_service.confirm_payroll_run(db, run_id)


# ── Payslips ──────────────────────────────────────────────────────────────────

@router.get("/payslips", response_model=PaginatedResponse[PaySlipResponse])
async def list_payslips(
    payroll_run_id: str | None = None,
    employee_id: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _=Depends(can_read(ModuleName.PAYROLL)),
    db: AsyncSession = Depends(get_db),
):
    slips, total = await payroll_service.list_payslips(db, payroll_run_id, employee_id, page, page_size)
    items = []
    for s in slips:
        emp = s.employee
        run = s.payroll_run
        period = run.pay_period if run else None
        items.append({
            "id":               s.id,
            "payroll_run_id":   s.payroll_run_id,
            "employee_id":      s.employee_id,
            "employee_name":    f"{emp.first_name} {emp.last_name}" if emp else None,
            "period_name":      f"FY{period.fiscal_year}-P{period.period_number:02d}" if period else None,
            "status":           run.status if run else None,
            "gross_pay":        s.gross_pay,
            "total_deductions": s.total_deductions,
            "net_pay":          s.net_pay,
            "income_tax":       s.income_tax,
            "employee_ni":      s.employee_ni,
            "employee_pension": s.employee_pension,
            "employer_ni":      s.employer_ni,
            "employer_pension": s.employer_pension,
            "line_items":       s.line_items,
            "is_anomalous":     s.is_anomalous,
            "anomaly_reason":   s.anomaly_reason,
        })
    return paginate(items, total, page, page_size)


@router.get("/payslips/{payslip_id}", response_model=PaySlipResponse)
async def get_payslip(
    payslip_id: str,
    _=Depends(can_read(ModuleName.PAYROLL)),
    db: AsyncSession = Depends(get_db),
):
    return await payroll_service.get_payslip(db, payslip_id)


# ── Pay Components ────────────────────────────────────────────────────────────

@router.get("/components", response_model=list[PayComponentResponse])
async def list_pay_components(
    _=Depends(can_read(ModuleName.PAYROLL)),
    db: AsyncSession = Depends(get_db),
):
    return await payroll_service.list_pay_components(db)


@router.post("/components", response_model=PayComponentResponse, status_code=201)
async def create_pay_component(
    data: PayComponentCreate,
    _=Depends(can_create(ModuleName.PAYROLL)),
    db: AsyncSession = Depends(get_db),
):
    return await payroll_service.create_pay_component(db, data)
