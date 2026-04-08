from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel


# ── Expense Category ──────────────────────────────────────────────────────────

class ExpenseCategoryCreate(BaseModel):
    code: str
    name: str
    daily_limit: Decimal | None = None
    requires_receipt: bool = True
    gl_account_code: str | None = None

class ExpenseCategoryResponse(ExpenseCategoryCreate):
    id: str
    is_active: bool
    model_config = {"from_attributes": True}


# ── Expense Line ──────────────────────────────────────────────────────────────

class ExpenseLineCreate(BaseModel):
    category_id: str
    expense_date: date
    merchant: str
    description: str | None = None
    amount: Decimal
    currency: str = "GBP"
    receipt_path: str | None = None
    is_billable: bool = False
    project_code: str | None = None

class ExpenseLineUpdate(BaseModel):
    merchant: str | None = None
    description: str | None = None
    amount: Decimal | None = None
    receipt_path: str | None = None

class ExpenseLineResponse(ExpenseLineCreate):
    id: str
    report_id: str
    is_violation: bool
    violation_type: str | None = None
    model_config = {"from_attributes": True}


# ── Expense Report ────────────────────────────────────────────────────────────

class ExpenseReportCreate(BaseModel):
    title: str
    period_start: date
    period_end: date
    currency: str = "GBP"
    lines: list[ExpenseLineCreate] = []

class ExpenseReportUpdate(BaseModel):
    title: str | None = None
    status: str | None = None

class ExpenseReportResponse(BaseModel):
    id: str
    report_number: str
    employee_id: str
    title: str
    period_start: date
    period_end: date
    total_amount: Decimal
    currency: str
    status: str
    approved_by: str | None = None
    rejection_reason: str | None = None
    violation_flags: dict | None = None
    violation_score: float | None = None
    is_flagged: bool
    lines: list[ExpenseLineResponse] = []
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

class ExpenseReportListResponse(BaseModel):
    id: str
    report_number: str
    employee_id: str
    title: str
    period_start: date
    period_end: date
    total_amount: Decimal
    currency: str
    status: str
    is_flagged: bool
    created_at: datetime
    model_config = {"from_attributes": True}

class ExpenseApproveRequest(BaseModel):
    approved_by: str

class ExpenseRejectRequest(BaseModel):
    reason: str
