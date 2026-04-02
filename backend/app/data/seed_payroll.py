"""
Seed Payroll — 3 years of monthly payroll history.
Embeds anomalies for ML detection:
  - Sudden salary spike (>50% jump)
  - Ghost employee (terminated but still paid)
  - Duplicate payslip in same period
  - Negative net pay
"""
import random
from datetime import date
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.payroll import PayGroup, PayPeriod, PayComponent, PayrollRun, PaySlip, PayFrequency, PayPeriodStatus, PayComponentType
from app.models.hcm import Employee

random.seed(42)

UK_TAX_RATE       = Decimal("0.20")
UK_NI_EMPLOYEE    = Decimal("0.12")
UK_NI_EMPLOYER    = Decimal("0.138")
PENSION_EMPLOYEE  = Decimal("0.05")
PENSION_EMPLOYER  = Decimal("0.03")


def calc_tax(gross: Decimal) -> Decimal:
    monthly_allowance = Decimal("1047.50")   # £12,570 / 12
    taxable = max(gross - monthly_allowance, Decimal("0"))
    return (taxable * UK_TAX_RATE).quantize(Decimal("0.01"))


def calc_ni(gross: Decimal) -> Decimal:
    lower = Decimal("1048")
    if gross <= lower:
        return Decimal("0")
    return ((gross - lower) * UK_NI_EMPLOYEE).quantize(Decimal("0.01"))


def calc_payslip(
    gross: Decimal,
    is_anomaly: bool = False,
    anomaly_type: str = "",
) -> dict:
    if is_anomaly and anomaly_type == "spike":
        gross = gross * Decimal("1.8")    # 80% spike
    elif is_anomaly and anomaly_type == "negative":
        gross = gross * Decimal("-0.1")

    tax      = calc_tax(gross)
    emp_ni   = calc_ni(gross)
    emp_pen  = (gross * PENSION_EMPLOYEE).quantize(Decimal("0.01"))
    emp_ni_e = (gross * UK_NI_EMPLOYER).quantize(Decimal("0.01"))
    emp_pen_e= (gross * PENSION_EMPLOYER).quantize(Decimal("0.01"))
    deductions = tax + emp_ni + emp_pen
    net      = gross - deductions

    return {
        "gross_pay":        gross,
        "total_deductions": deductions,
        "net_pay":          net,
        "income_tax":       tax,
        "employee_ni":      emp_ni,
        "employee_pension": emp_pen,
        "employer_ni":      emp_ni_e,
        "employer_pension": emp_pen_e,
        "line_items": {
            "basic_pay":        float(gross),
            "income_tax":       float(tax),
            "employee_ni":      float(emp_ni),
            "employee_pension": float(emp_pen),
        },
    }


async def run(db: AsyncSession, employees: list) -> None:
    print("Seeding Payroll...")

    result = await db.execute(select(func.count()).select_from(PayGroup))
    if result.scalar() > 0:
        print("  Payroll already seeded — skipping")
        return

    # ── Pay group ──────────────────────────────────────────────────────────────
    pay_group = PayGroup(code="PG-GB-MONTHLY", name="UK Monthly Payroll", frequency=PayFrequency.MONTHLY, currency="GBP")
    db.add(pay_group)
    await db.flush()

    # ── Pay components ────────────────────────────────────────────────────────
    components = [
        PayComponent(code="BASIC",  name="Basic Pay",          component_type=PayComponentType.EARNING,               is_taxable=True,  is_pensionable=True,  gl_account_code="6100"),
        PayComponent(code="BONUS",  name="Performance Bonus",  component_type=PayComponentType.EARNING,               is_taxable=True,  is_pensionable=False, gl_account_code="6110"),
        PayComponent(code="ITAX",   name="Income Tax",         component_type=PayComponentType.TAX,                   is_taxable=False, is_pensionable=False, gl_account_code="2100"),
        PayComponent(code="EMPNI",  name="Employee NI",        component_type=PayComponentType.DEDUCTION,             is_taxable=False, is_pensionable=False, gl_account_code="2110"),
        PayComponent(code="ERNI",   name="Employer NI",        component_type=PayComponentType.EMPLOYER_CONTRIBUTION, is_taxable=False, is_pensionable=False, gl_account_code="6200"),
        PayComponent(code="EMPPEN", name="Employee Pension",   component_type=PayComponentType.DEDUCTION,             is_taxable=False, is_pensionable=False, gl_account_code="2120"),
        PayComponent(code="ERPEN",  name="Employer Pension",   component_type=PayComponentType.EMPLOYER_CONTRIBUTION, is_taxable=False, is_pensionable=False, gl_account_code="6210"),
    ]
    for c in components:
        db.add(c)
    await db.flush()

    # ── 3 years of monthly periods ────────────────────────────────────────────
    active_employees = [e for e in employees if e.is_active or e.termination_date]
    start_date = date.today().replace(day=1) - relativedelta(months=36)

    period_num = 1
    total_payslips = 0
    anomaly_count  = 0

    for month_offset in range(36):
        period_start = start_date + relativedelta(months=month_offset)
        period_end   = period_start + relativedelta(months=1) - relativedelta(days=1)
        pay_date     = period_start + relativedelta(months=1, day=28)
        year         = period_start.year
        is_closed    = period_end < date.today()

        period = PayPeriod(
            pay_group_id=pay_group.id,
            period_number=period_num,
            fiscal_year=year,
            start_date=period_start,
            end_date=period_end,
            pay_date=pay_date,
            status=PayPeriodStatus.CLOSED if is_closed else PayPeriodStatus.OPEN,
        )
        db.add(period)
        await db.flush()

        run = PayrollRun(
            pay_period_id=period.id,
            run_number=1,
            status="confirmed" if is_closed else "draft",
        )
        db.add(run)
        await db.flush()

        run_gross = Decimal("0")
        run_deductions = Decimal("0")
        run_net = Decimal("0")

        for emp in active_employees:
            # Skip if employee not yet hired or already terminated before period
            if emp.hire_date > period_end:
                continue
            if emp.termination_date and emp.termination_date < period_start:
                # Ghost employee anomaly — 2% chance still gets paid after termination
                if random.random() > 0.02:
                    continue

            monthly_gross = (emp.base_salary / 12).quantize(Decimal("0.01"))

            # Determine anomaly (2% of payslips)
            is_anomaly   = random.random() < 0.02
            anomaly_type = ""
            if is_anomaly:
                anomaly_type = random.choice(["spike", "negative", "duplicate"])
                anomaly_count += 1

            data = calc_payslip(monthly_gross, is_anomaly, anomaly_type)

            slip = PaySlip(
                payroll_run_id=run.id,
                employee_id=emp.id,
                is_anomalous=is_anomaly,
                anomaly_reason=anomaly_type if is_anomaly else None,
                **data,
            )
            db.add(slip)

            # Duplicate payslip anomaly
            if is_anomaly and anomaly_type == "duplicate":
                db.add(PaySlip(
                    payroll_run_id=run.id,
                    employee_id=emp.id,
                    is_anomalous=True,
                    anomaly_reason="duplicate",
                    **data,
                ))

            run_gross      += data["gross_pay"]
            run_deductions += data["total_deductions"]
            run_net        += data["net_pay"]
            total_payslips += 1

        run.total_gross      = run_gross
        run.total_deductions = run_deductions
        run.total_net        = run_net
        period_num += 1

    await db.commit()
    print(f"  Created 36 pay periods, ~{total_payslips} payslips, {anomaly_count} anomalies")
