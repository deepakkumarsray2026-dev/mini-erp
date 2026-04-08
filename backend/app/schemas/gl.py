from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, model_validator


# ── Chart of Accounts ─────────────────────────────────────────────────────────

class AccountCreate(BaseModel):
    account_code: str
    account_name: str
    account_type: str
    parent_code: str | None = None
    description: str | None = None
    is_control_account: bool = False
    currency: str = "GBP"
    normal_balance: str = "debit"

class AccountUpdate(BaseModel):
    account_name: str | None = None
    description: str | None = None
    is_active: bool | None = None

class AccountResponse(AccountCreate):
    id: str
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Fiscal Period ─────────────────────────────────────────────────────────────

class FiscalPeriodCreate(BaseModel):
    fiscal_year: int
    period_number: int
    name: str
    start_date: date
    end_date: date

class FiscalPeriodResponse(FiscalPeriodCreate):
    id: str
    status: str
    model_config = {"from_attributes": True}


# ── Journal Line ──────────────────────────────────────────────────────────────

class JournalLineCreate(BaseModel):
    account_code: str
    description: str | None = None
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    department_id: str | None = None
    cost_center: str | None = None
    project_code: str | None = None

class JournalLineResponse(JournalLineCreate):
    id: str
    journal_id: str
    model_config = {"from_attributes": True}


# ── Journal ───────────────────────────────────────────────────────────────────

class JournalCreate(BaseModel):
    fiscal_period_id: str
    journal_date: date
    description: str
    source: str = "manual"
    currency: str = "GBP"
    lines: list[JournalLineCreate]

    @model_validator(mode="after")
    def check_balanced(self) -> "JournalCreate":
        total_debit  = sum(l.debit  for l in self.lines)
        total_credit = sum(l.credit for l in self.lines)
        if abs(total_debit - total_credit) > Decimal("0.01"):
            raise ValueError(f"Journal must balance: debits={total_debit} credits={total_credit}")
        return self

class JournalUpdate(BaseModel):
    description: str | None = None
    status: str | None = None

class JournalResponse(BaseModel):
    id: str
    journal_number: str
    fiscal_period_id: str
    journal_date: date
    description: str
    source: str
    total_debit: Decimal
    total_credit: Decimal
    is_balanced: bool
    status: str
    currency: str
    posted_at: datetime | None = None
    lines: list[JournalLineResponse] = []
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Budget ────────────────────────────────────────────────────────────────────

class BudgetCreate(BaseModel):
    fiscal_year: int
    period_number: int
    account_code: str
    department_id: str | None = None
    budgeted_amount: Decimal
    currency: str = "GBP"

class BudgetUpdate(BaseModel):
    budgeted_amount: Decimal | None = None
    forecasted_amount: Decimal | None = None

class BudgetResponse(BudgetCreate):
    id: str
    actual_amount: Decimal
    forecasted_amount: Decimal | None = None
    variance: Decimal
    model_config = {"from_attributes": True}


# ── Trial Balance ─────────────────────────────────────────────────────────────

class TrialBalanceLine(BaseModel):
    account_code: str
    account_name: str
    account_type: str
    total_debit: Decimal
    total_credit: Decimal
    balance: Decimal
