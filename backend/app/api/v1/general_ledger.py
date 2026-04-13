"""
General Ledger API  —  Chart of Accounts, Fiscal Periods, Journals, Budgets, Trial Balance
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import (
    can_read, can_create, can_update, can_approve,
    ModuleName, get_current_user,
)
from app.schemas.gl import (
    AccountCreate, AccountUpdate, AccountResponse,
    FiscalPeriodCreate, FiscalPeriodResponse,
    JournalCreate, JournalUpdate, JournalResponse,
    BudgetCreate, BudgetUpdate, BudgetResponse,
    TrialBalanceLine,
)
from app.schemas.common import PaginatedResponse, MessageResponse, paginate
from app.services import gl_service

router = APIRouter()


# ── Chart of Accounts ─────────────────────────────────────────────────────────

@router.get("/accounts", response_model=PaginatedResponse[AccountResponse])
async def list_accounts(
    account_type: str | None = None,
    active_only: bool = True,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _=Depends(can_read(ModuleName.GL)),
    db: AsyncSession = Depends(get_db),
):
    items, total = await gl_service.list_accounts(db, account_type, active_only, page, page_size)
    return paginate(items, total, page, page_size)


@router.post("/accounts", response_model=AccountResponse, status_code=201)
async def create_account(
    data: AccountCreate,
    _=Depends(can_create(ModuleName.GL)),
    db: AsyncSession = Depends(get_db),
):
    return await gl_service.create_account(db, data)


@router.get("/accounts/{account_code}", response_model=AccountResponse)
async def get_account(
    account_code: str,
    _=Depends(can_read(ModuleName.GL)),
    db: AsyncSession = Depends(get_db),
):
    return await gl_service.get_account(db, account_code)


@router.patch("/accounts/{account_code}", response_model=AccountResponse)
async def update_account(
    account_code: str,
    data: AccountUpdate,
    _=Depends(can_update(ModuleName.GL)),
    db: AsyncSession = Depends(get_db),
):
    return await gl_service.update_account(db, account_code, data)


# ── Fiscal Periods ────────────────────────────────────────────────────────────

@router.get("/fiscal-periods", response_model=list[FiscalPeriodResponse])
async def list_fiscal_periods(
    fiscal_year: int | None = None,
    _=Depends(can_read(ModuleName.GL)),
    db: AsyncSession = Depends(get_db),
):
    return await gl_service.list_fiscal_periods(db, fiscal_year)


@router.post("/fiscal-periods", response_model=FiscalPeriodResponse, status_code=201)
async def create_fiscal_period(
    data: FiscalPeriodCreate,
    _=Depends(can_create(ModuleName.GL)),
    db: AsyncSession = Depends(get_db),
):
    return await gl_service.create_fiscal_period(db, data)


@router.post("/fiscal-periods/{period_id}/close", response_model=FiscalPeriodResponse)
async def close_fiscal_period(
    period_id: str,
    _=Depends(can_approve(ModuleName.GL)),
    db: AsyncSession = Depends(get_db),
):
    return await gl_service.close_fiscal_period(db, period_id)


# ── Journals ──────────────────────────────────────────────────────────────────

@router.get("/journals", response_model=PaginatedResponse[JournalResponse])
async def list_journals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    fiscal_period_id: str | None = None,
    source: str | None = None,
    status: str | None = None,
    _=Depends(can_read(ModuleName.GL)),
    db: AsyncSession = Depends(get_db),
):
    journals, total = await gl_service.list_journals(db, fiscal_period_id, source, status, page, page_size)
    return paginate(journals, total, page, page_size)


@router.post("/journals", response_model=JournalResponse, status_code=201)
async def create_journal(
    data: JournalCreate,
    ctx=Depends(can_create(ModuleName.GL)),
    db: AsyncSession = Depends(get_db),
):
    return await gl_service.create_journal(db, data, posted_by=ctx.user.id)


@router.get("/journals/{journal_id}", response_model=JournalResponse)
async def get_journal(
    journal_id: str,
    _=Depends(can_read(ModuleName.GL)),
    db: AsyncSession = Depends(get_db),
):
    return await gl_service.get_journal(db, journal_id)


@router.post("/journals/{journal_id}/post", response_model=JournalResponse)
async def post_journal(
    journal_id: str,
    _=Depends(can_approve(ModuleName.GL)),
    db: AsyncSession = Depends(get_db),
):
    return await gl_service.post_journal(db, journal_id)


@router.post("/journals/{journal_id}/void", response_model=JournalResponse)
async def void_journal(
    journal_id: str,
    _=Depends(can_approve(ModuleName.GL)),
    db: AsyncSession = Depends(get_db),
):
    return await gl_service.void_journal(db, journal_id)


# ── Budgets ───────────────────────────────────────────────────────────────────

@router.get("/budgets", response_model=list[BudgetResponse])
async def list_budgets(
    fiscal_year: int | None = None,
    department_id: str | None = None,
    _=Depends(can_read(ModuleName.GL)),
    db: AsyncSession = Depends(get_db),
):
    return await gl_service.list_budgets(db, fiscal_year, department_id)


@router.post("/budgets", response_model=BudgetResponse, status_code=201)
async def create_budget(
    data: BudgetCreate,
    _=Depends(can_create(ModuleName.GL)),
    db: AsyncSession = Depends(get_db),
):
    return await gl_service.create_budget(db, data)


@router.patch("/budgets/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: str,
    data: BudgetUpdate,
    _=Depends(can_update(ModuleName.GL)),
    db: AsyncSession = Depends(get_db),
):
    return await gl_service.update_budget(db, budget_id, data)


# ── Trial Balance ─────────────────────────────────────────────────────────────

@router.get("/trial-balance", response_model=list[TrialBalanceLine])
async def get_trial_balance(
    fiscal_year: int | None = Query(None, description="Fiscal year e.g. 2025, defaults to current year"),
    period_number: int | None = Query(None, description="Up to and including this period"),
    _=Depends(can_read(ModuleName.GL)),
    db: AsyncSession = Depends(get_db),
):
    from datetime import date
    year = fiscal_year or date.today().year
    return await gl_service.get_trial_balance(db, year, period_number)
