"""
gl_service.py  —  General Ledger: CoA, Journals, Budgets, Trial Balance
"""
from datetime import date
from decimal import Decimal
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.models.gl import ChartOfAccounts, FiscalPeriod, Journal, JournalLine, Budget, JournalSource
from app.schemas.gl import (
    AccountCreate, AccountUpdate,
    FiscalPeriodCreate,
    JournalCreate, JournalUpdate,
    BudgetCreate, BudgetUpdate,
    TrialBalanceLine,
)


# ── Chart of Accounts ─────────────────────────────────────────────────────────

async def list_accounts(db: AsyncSession, account_type: str | None = None, active_only: bool = True) -> list[ChartOfAccounts]:
    q = select(ChartOfAccounts)
    if active_only:
        q = q.where(ChartOfAccounts.is_active == True)
    if account_type:
        q = q.where(ChartOfAccounts.account_type == account_type)
    result = await db.execute(q.order_by(ChartOfAccounts.account_code))
    return result.scalars().all()


async def get_account(db: AsyncSession, account_code: str) -> ChartOfAccounts:
    result = await db.execute(select(ChartOfAccounts).where(ChartOfAccounts.account_code == account_code))
    acct = result.scalar_one_or_none()
    if not acct:
        raise HTTPException(status_code=404, detail=f"Account '{account_code}' not found")
    return acct


async def create_account(db: AsyncSession, data: AccountCreate) -> ChartOfAccounts:
    existing = await db.execute(select(ChartOfAccounts).where(ChartOfAccounts.account_code == data.account_code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Account code '{data.account_code}' already exists")
    if data.parent_code:
        await get_account(db, data.parent_code)   # validate parent exists
    acct = ChartOfAccounts(**data.model_dump())
    db.add(acct)
    await db.flush()
    await db.refresh(acct)
    return acct


async def update_account(db: AsyncSession, account_code: str, data: AccountUpdate) -> ChartOfAccounts:
    acct = await get_account(db, account_code)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(acct, field, value)
    await db.flush()
    await db.refresh(acct)
    return acct


# ── Fiscal Periods ────────────────────────────────────────────────────────────

async def list_fiscal_periods(db: AsyncSession, fiscal_year: int | None = None) -> list[FiscalPeriod]:
    q = select(FiscalPeriod)
    if fiscal_year:
        q = q.where(FiscalPeriod.fiscal_year == fiscal_year)
    result = await db.execute(q.order_by(FiscalPeriod.fiscal_year, FiscalPeriod.period_number))
    return result.scalars().all()


async def get_fiscal_period(db: AsyncSession, period_id: str) -> FiscalPeriod:
    result = await db.execute(select(FiscalPeriod).where(FiscalPeriod.id == period_id))
    fp = result.scalar_one_or_none()
    if not fp:
        raise HTTPException(status_code=404, detail="Fiscal period not found")
    return fp


async def create_fiscal_period(db: AsyncSession, data: FiscalPeriodCreate) -> FiscalPeriod:
    existing = await db.execute(
        select(FiscalPeriod).where(
            FiscalPeriod.fiscal_year   == data.fiscal_year,
            FiscalPeriod.period_number == data.period_number,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Fiscal period already exists")
    fp = FiscalPeriod(**data.model_dump())
    db.add(fp)
    await db.flush()
    await db.refresh(fp)
    return fp


async def close_fiscal_period(db: AsyncSession, period_id: str) -> FiscalPeriod:
    fp = await get_fiscal_period(db, period_id)
    if fp.status == "closed":
        raise HTTPException(status_code=409, detail="Period is already closed")
    fp.status = "closed"
    await db.flush()
    await db.refresh(fp)
    return fp


# ── Journals ──────────────────────────────────────────────────────────────────

async def list_journals(
    db: AsyncSession,
    fiscal_period_id: str | None = None,
    source: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Journal], int]:
    q = select(Journal)
    if fiscal_period_id:
        q = q.where(Journal.fiscal_period_id == fiscal_period_id)
    if source:
        q = q.where(Journal.source == source)
    if status:
        q = q.where(Journal.status == status)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    result = await db.execute(
        q.order_by(Journal.journal_date.desc(), Journal.created_at.desc())
         .offset((page - 1) * page_size).limit(page_size)
    )
    return result.scalars().all(), total


async def get_journal(db: AsyncSession, journal_id: str) -> Journal:
    result = await db.execute(
        select(Journal).where(Journal.id == journal_id)
        .options(selectinload(Journal.lines))
    )
    j = result.scalar_one_or_none()
    if not j:
        raise HTTPException(status_code=404, detail="Journal not found")
    return j


async def create_journal(db: AsyncSession, data: JournalCreate, posted_by: str) -> Journal:
    fp = await get_fiscal_period(db, data.fiscal_period_id)
    if fp.status == "closed":
        raise HTTPException(status_code=409, detail="Cannot post to a closed fiscal period")

    count = (await db.execute(select(func.count(Journal.id)))).scalar() or 0
    lines_data = data.model_dump(exclude={"lines"})

    total_debit  = sum(l.debit  for l in data.lines)
    total_credit = sum(l.credit for l in data.lines)

    journal = Journal(
        **lines_data,
        journal_number=f"JNL-{count + 1:06d}",
        total_debit=total_debit,
        total_credit=total_credit,
        is_balanced=True,
        posted_by=posted_by,
        status="draft",
    )
    db.add(journal)
    await db.flush()

    for line_data in data.lines:
        # validate account exists
        await get_account(db, line_data.account_code)
        line = JournalLine(**line_data.model_dump(), journal_id=journal.id)
        db.add(line)

    await db.flush()
    await db.refresh(journal)
    return journal


async def post_journal(db: AsyncSession, journal_id: str) -> Journal:
    from datetime import datetime, timezone
    journal = await get_journal(db, journal_id)
    if journal.status == "posted":
        raise HTTPException(status_code=409, detail="Journal is already posted")
    if not journal.is_balanced:
        raise HTTPException(status_code=422, detail="Journal is not balanced")
    journal.status    = "posted"
    journal.posted_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(journal)
    return journal


async def void_journal(db: AsyncSession, journal_id: str) -> Journal:
    journal = await get_journal(db, journal_id)
    if journal.status == "voided":
        raise HTTPException(status_code=409, detail="Journal is already voided")
    journal.status = "voided"
    await db.flush()
    await db.refresh(journal)
    return journal


# ── Budgets ───────────────────────────────────────────────────────────────────

async def list_budgets(
    db: AsyncSession,
    fiscal_year: int | None = None,
    department_id: str | None = None,
) -> list[Budget]:
    q = select(Budget)
    if fiscal_year:
        q = q.where(Budget.fiscal_year == fiscal_year)
    if department_id:
        q = q.where(Budget.department_id == department_id)
    result = await db.execute(q.order_by(Budget.fiscal_year, Budget.period_number, Budget.account_code))
    return result.scalars().all()


async def get_budget(db: AsyncSession, budget_id: str) -> Budget:
    result = await db.execute(select(Budget).where(Budget.id == budget_id))
    b = result.scalar_one_or_none()
    if not b:
        raise HTTPException(status_code=404, detail="Budget not found")
    return b


async def create_budget(db: AsyncSession, data: BudgetCreate) -> Budget:
    await get_account(db, data.account_code)   # validate account
    budget = Budget(**data.model_dump())
    db.add(budget)
    await db.flush()
    await db.refresh(budget)
    return budget


async def update_budget(db: AsyncSession, budget_id: str, data: BudgetUpdate) -> Budget:
    budget = await get_budget(db, budget_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(budget, field, value)
    if budget.budgeted_amount:
        budget.variance = budget.actual_amount - budget.budgeted_amount
    await db.flush()
    await db.refresh(budget)
    return budget


# ── Trial Balance ─────────────────────────────────────────────────────────────

async def get_trial_balance(
    db: AsyncSession,
    fiscal_year: int,
    period_number: int | None = None,
) -> list[TrialBalanceLine]:
    """Aggregate posted journal lines into a trial balance."""
    conditions = ["j.status = 'posted'", f"fp.fiscal_year = {fiscal_year}"]
    if period_number:
        conditions.append(f"fp.period_number <= {period_number}")

    where_clause = " AND ".join(conditions)

    query = text(f"""
        SELECT
            coa.account_code,
            coa.account_name,
            coa.account_type,
            COALESCE(SUM(jl.debit),  0) AS total_debit,
            COALESCE(SUM(jl.credit), 0) AS total_credit,
            COALESCE(SUM(jl.debit) - SUM(jl.credit), 0) AS balance
        FROM gl.chart_of_accounts coa
        LEFT JOIN gl.journal_lines jl  ON jl.account_code = coa.account_code
        LEFT JOIN gl.journals j        ON j.id = jl.journal_id
        LEFT JOIN gl.fiscal_periods fp ON fp.id = j.fiscal_period_id
        WHERE coa.is_active = true AND ({where_clause} OR jl.id IS NULL)
        GROUP BY coa.account_code, coa.account_name, coa.account_type
        HAVING COALESCE(SUM(jl.debit), 0) > 0 OR COALESCE(SUM(jl.credit), 0) > 0
        ORDER BY coa.account_code
    """)

    result = await db.execute(query)
    rows = result.fetchall()
    return [
        TrialBalanceLine(
            account_code=r[0],
            account_name=r[1],
            account_type=r[2],
            total_debit=Decimal(str(r[3])),
            total_credit=Decimal(str(r[4])),
            balance=Decimal(str(r[5])),
        )
        for r in rows
    ]
