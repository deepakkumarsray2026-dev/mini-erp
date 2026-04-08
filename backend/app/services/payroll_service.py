"""
payroll_service.py  —  Payroll CRUD & run service
"""
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.payroll import PayGroup, PayPeriod, PayPeriodStatus, PayrollRun, PaySlip, PayComponent
from app.models.hcm import Employee
from app.schemas.payroll import PayGroupCreate, PayrollRunCreate, PayComponentCreate


# ── Pay Groups ────────────────────────────────────────────────────────────────

async def list_pay_groups(db: AsyncSession) -> list[PayGroup]:
    result = await db.execute(select(PayGroup).where(PayGroup.is_active == True))
    return result.scalars().all()


async def create_pay_group(db: AsyncSession, data: PayGroupCreate) -> PayGroup:
    existing = await db.execute(select(PayGroup).where(PayGroup.code == data.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Pay group code '{data.code}' already exists")
    pg = PayGroup(**data.model_dump())
    db.add(pg)
    await db.flush()
    await db.refresh(pg)
    return pg


# ── Pay Periods ───────────────────────────────────────────────────────────────

async def list_pay_periods(db: AsyncSession, pay_group_id: str | None = None, fiscal_year: int | None = None) -> list[PayPeriod]:
    q = select(PayPeriod)
    if pay_group_id:
        q = q.where(PayPeriod.pay_group_id == pay_group_id)
    if fiscal_year:
        q = q.where(PayPeriod.fiscal_year == fiscal_year)
    result = await db.execute(q.order_by(PayPeriod.start_date.desc()))
    return result.scalars().all()


async def get_pay_period(db: AsyncSession, period_id: str) -> PayPeriod:
    result = await db.execute(select(PayPeriod).where(PayPeriod.id == period_id))
    pp = result.scalar_one_or_none()
    if not pp:
        raise HTTPException(status_code=404, detail="Pay period not found")
    return pp


# ── Payroll Runs ──────────────────────────────────────────────────────────────

async def list_payroll_runs(db: AsyncSession, pay_period_id: str | None = None) -> list[PayrollRun]:
    q = select(PayrollRun)
    if pay_period_id:
        q = q.where(PayrollRun.pay_period_id == pay_period_id)
    result = await db.execute(q.order_by(PayrollRun.created_at.desc()))
    return result.scalars().all()


async def get_payroll_run(db: AsyncSession, run_id: str) -> PayrollRun:
    result = await db.execute(select(PayrollRun).where(PayrollRun.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Payroll run not found")
    return run


async def create_payroll_run(db: AsyncSession, data: PayrollRunCreate, run_by: str) -> PayrollRun:
    pp = await get_pay_period(db, data.pay_period_id)
    if pp.status == PayPeriodStatus.CLOSED:
        raise HTTPException(status_code=409, detail="Pay period is closed")

    # Get run number
    count_res = await db.execute(
        select(func.count(PayrollRun.id)).where(PayrollRun.pay_period_id == data.pay_period_id)
    )
    run_number = (count_res.scalar() or 0) + 1

    run = PayrollRun(
        pay_period_id=data.pay_period_id,
        run_number=run_number,
        status="draft",
        run_by=run_by,
    )
    db.add(run)
    await db.flush()

    # Calculate payslips for all active employees
    employees_result = await db.execute(
        select(Employee).where(Employee.is_active == True)
    )
    employees = employees_result.scalars().all()

    total_gross = Decimal("0")
    total_deductions = Decimal("0")
    total_net = Decimal("0")
    total_employer_ni = Decimal("0")
    total_employer_pension = Decimal("0")

    for emp in employees:
        monthly_gross = emp.base_salary / 12

        # UK tax calculation (simplified)
        annual_allowance = Decimal("12570")
        annual_taxable   = max(emp.base_salary - annual_allowance, Decimal("0"))
        if annual_taxable <= Decimal("37700"):
            income_tax = (annual_taxable * Decimal("0.20")) / 12
        elif annual_taxable <= Decimal("125140"):
            income_tax = (Decimal("37700") * Decimal("0.20") + (annual_taxable - Decimal("37700")) * Decimal("0.40")) / 12
        else:
            income_tax = (Decimal("37700") * Decimal("0.20") + Decimal("87440") * Decimal("0.40") + (annual_taxable - Decimal("125140")) * Decimal("0.45")) / 12

        # NI (simplified class 1)
        ni_threshold = Decimal("1048")   # monthly primary threshold
        ni_upper     = Decimal("4189")
        if monthly_gross <= ni_threshold:
            employee_ni = Decimal("0")
            employer_ni = Decimal("0")
        elif monthly_gross <= ni_upper:
            employee_ni = (monthly_gross - ni_threshold) * Decimal("0.12")
            employer_ni = (monthly_gross - ni_threshold) * Decimal("0.1385")
        else:
            employee_ni = (ni_upper - ni_threshold) * Decimal("0.12") + (monthly_gross - ni_upper) * Decimal("0.02")
            employer_ni = (monthly_gross - ni_threshold) * Decimal("0.1385")

        # Pension (auto-enrolment 5% employee / 3% employer)
        employee_pension = monthly_gross * Decimal("0.05")
        employer_pension = monthly_gross * Decimal("0.03")

        total_deductions_slip = income_tax + employee_ni + employee_pension
        net_pay = monthly_gross - total_deductions_slip

        slip = PaySlip(
            payroll_run_id=run.id,
            employee_id=emp.id,
            gross_pay=monthly_gross.quantize(Decimal("0.01")),
            total_deductions=total_deductions_slip.quantize(Decimal("0.01")),
            net_pay=net_pay.quantize(Decimal("0.01")),
            income_tax=income_tax.quantize(Decimal("0.01")),
            employee_ni=employee_ni.quantize(Decimal("0.01")),
            employee_pension=employee_pension.quantize(Decimal("0.01")),
            employer_ni=employer_ni.quantize(Decimal("0.01")),
            employer_pension=employer_pension.quantize(Decimal("0.01")),
            line_items={
                "base_salary": str(monthly_gross),
                "income_tax":  str(income_tax.quantize(Decimal("0.01"))),
                "employee_ni": str(employee_ni.quantize(Decimal("0.01"))),
                "pension":     str(employee_pension.quantize(Decimal("0.01"))),
            },
        )
        db.add(slip)

        total_gross         += monthly_gross
        total_deductions    += total_deductions_slip
        total_net           += net_pay
        total_employer_ni   += employer_ni
        total_employer_pension += employer_pension

    run.total_gross            = total_gross.quantize(Decimal("0.01"))
    run.total_deductions       = total_deductions.quantize(Decimal("0.01"))
    run.total_net              = total_net.quantize(Decimal("0.01"))
    run.total_employer_ni      = total_employer_ni.quantize(Decimal("0.01"))
    run.total_employer_pension = total_employer_pension.quantize(Decimal("0.01"))
    run.status                 = "calculated"
    run.run_at                 = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(run)
    return run


async def confirm_payroll_run(db: AsyncSession, run_id: str) -> PayrollRun:
    run = await get_payroll_run(db, run_id)
    if run.status not in ("calculated", "draft"):
        raise HTTPException(status_code=409, detail=f"Cannot confirm run with status '{run.status}'")
    run.status = "confirmed"
    await db.flush()
    await db.refresh(run)
    return run


# ── Payslips ──────────────────────────────────────────────────────────────────

async def list_payslips(db: AsyncSession, payroll_run_id: str | None = None, employee_id: str | None = None) -> list[PaySlip]:
    q = select(PaySlip)
    if payroll_run_id:
        q = q.where(PaySlip.payroll_run_id == payroll_run_id)
    if employee_id:
        q = q.where(PaySlip.employee_id == employee_id)
    result = await db.execute(q.order_by(PaySlip.created_at.desc()))
    return result.scalars().all()


async def get_payslip(db: AsyncSession, payslip_id: str) -> PaySlip:
    result = await db.execute(select(PaySlip).where(PaySlip.id == payslip_id))
    slip = result.scalar_one_or_none()
    if not slip:
        raise HTTPException(status_code=404, detail="Payslip not found")
    return slip


# ── Pay Components ────────────────────────────────────────────────────────────

async def list_pay_components(db: AsyncSession) -> list[PayComponent]:
    result = await db.execute(select(PayComponent).where(PayComponent.is_active == True))
    return result.scalars().all()


async def create_pay_component(db: AsyncSession, data: PayComponentCreate) -> PayComponent:
    existing = await db.execute(select(PayComponent).where(PayComponent.code == data.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Pay component '{data.code}' already exists")
    pc = PayComponent(**data.model_dump())
    db.add(pc)
    await db.flush()
    await db.refresh(pc)
    return pc
