from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel


# ── Pay Group ─────────────────────────────────────────────────────────────────

class PayGroupCreate(BaseModel):
    code: str
    name: str
    frequency: str
    currency: str = "GBP"

class PayGroupResponse(PayGroupCreate):
    id: str
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Pay Period ────────────────────────────────────────────────────────────────

class PayPeriodResponse(BaseModel):
    id: str
    pay_group_id: str
    period_name: str | None = None
    pay_group_name: str | None = None
    period_number: int
    fiscal_year: int
    start_date: date
    end_date: date
    pay_date: date
    status: str
    model_config = {"from_attributes": True}


# ── Payroll Run ───────────────────────────────────────────────────────────────

class PayrollRunResponse(BaseModel):
    id: str
    pay_period_id: str
    run_number: int
    status: str
    total_gross: Decimal
    total_deductions: Decimal
    total_net: Decimal
    total_employer_ni: Decimal
    total_employer_pension: Decimal
    run_at: datetime | None = None
    anomaly_flags: dict | None = None
    model_config = {"from_attributes": True}

class PayrollRunCreate(BaseModel):
    pay_period_id: str


# ── PaySlip ───────────────────────────────────────────────────────────────────

class PaySlipResponse(BaseModel):
    id: str
    payroll_run_id: str
    employee_id: str
    employee_name: str | None = None
    period_name: str | None = None
    status: str | None = None
    gross_pay: Decimal
    total_deductions: Decimal
    net_pay: Decimal
    income_tax: Decimal
    employee_ni: Decimal
    employee_pension: Decimal
    employer_ni: Decimal
    employer_pension: Decimal
    line_items: dict
    is_anomalous: bool
    anomaly_reason: str | None = None
    model_config = {"from_attributes": True}


# ── Pay Component ─────────────────────────────────────────────────────────────

class PayComponentCreate(BaseModel):
    code: str
    name: str
    component_type: str
    is_taxable: bool = True
    is_pensionable: bool = True
    gl_account_code: str | None = None

class PayComponentResponse(PayComponentCreate):
    id: str
    is_active: bool
    model_config = {"from_attributes": True}
