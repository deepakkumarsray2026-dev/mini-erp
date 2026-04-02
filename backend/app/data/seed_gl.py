"""
Seed GL — chart of accounts, fiscal periods, journals, budgets.
"""
import random
from datetime import date
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.gl import ChartOfAccounts, FiscalPeriod, Journal, JournalLine, Budget, AccountType, JournalSource

random.seed(42)

COA = [
    # (code, name, type, parent, normal_balance)
    ("1000", "Current Assets",          AccountType.ASSET,     None,   "debit"),
    ("1100", "Cash and Bank",           AccountType.ASSET,     "1000", "debit"),
    ("1200", "Accounts Receivable",     AccountType.ASSET,     "1000", "debit"),
    ("1300", "Prepaid Expenses",        AccountType.ASSET,     "1000", "debit"),
    ("2000", "Current Liabilities",     AccountType.LIABILITY, None,   "credit"),
    ("2100", "Income Tax Payable",      AccountType.LIABILITY, "2000", "credit"),
    ("2110", "NI Payable",              AccountType.LIABILITY, "2000", "credit"),
    ("2120", "Pension Payable",         AccountType.LIABILITY, "2000", "credit"),
    ("2200", "Accounts Payable",        AccountType.LIABILITY, "2000", "credit"),
    ("3000", "Equity",                  AccountType.EQUITY,    None,   "credit"),
    ("3100", "Retained Earnings",       AccountType.EQUITY,    "3000", "credit"),
    ("4000", "Revenue",                 AccountType.REVENUE,   None,   "credit"),
    ("4100", "Product Revenue",         AccountType.REVENUE,   "4000", "credit"),
    ("4200", "Service Revenue",         AccountType.REVENUE,   "4000", "credit"),
    ("5000", "Cost of Goods Sold",      AccountType.EXPENSE,   None,   "debit"),
    ("6000", "Operating Expenses",      AccountType.EXPENSE,   None,   "debit"),
    ("6100", "Salaries — Basic Pay",    AccountType.EXPENSE,   "6000", "debit"),
    ("6110", "Salaries — Bonus",        AccountType.EXPENSE,   "6000", "debit"),
    ("6200", "Employer NI",             AccountType.EXPENSE,   "6000", "debit"),
    ("6210", "Employer Pension",        AccountType.EXPENSE,   "6000", "debit"),
    ("6300", "Office Expenses",         AccountType.EXPENSE,   "6000", "debit"),
    ("6400", "IT & Software",           AccountType.EXPENSE,   "6000", "debit"),
    ("6500", "Travel & Entertainment",  AccountType.EXPENSE,   "6000", "debit"),
    ("6600", "Marketing",               AccountType.EXPENSE,   "6000", "debit"),
    ("6700", "Professional Services",   AccountType.EXPENSE,   "6000", "debit"),
    ("6800", "Utilities",               AccountType.EXPENSE,   "6000", "debit"),
    ("6900", "Depreciation",            AccountType.EXPENSE,   "6000", "debit"),
    ("7000", "Other Expenses",          AccountType.EXPENSE,   "6000", "debit"),
]


async def run(db: AsyncSession) -> None:
    print("Seeding GL...")

    result = await db.execute(select(func.count()).select_from(ChartOfAccounts))
    if result.scalar() > 0:
        print("  GL already seeded — skipping")
        return

    # ── Chart of accounts ─────────────────────────────────────────────────────
    coa_map = {}
    for code, name, acc_type, parent, normal in COA:
        acc = ChartOfAccounts(
            account_code=code,
            account_name=name,
            account_type=acc_type,
            parent_code=parent,
            normal_balance=normal,
            is_active=True,
        )
        db.add(acc)
        coa_map[code] = acc
    await db.flush()
    print(f"  Created {len(coa_map)} accounts")

    # ── Fiscal periods (3 years) ───────────────────────────────────────────────
    today      = date.today()
    start_year = today.year - 2
    periods    = []

    for year_offset in range(3):
        year = start_year + year_offset
        for month in range(1, 13):
            period_date  = date(year, month, 1)
            period_end   = period_date + relativedelta(months=1) - relativedelta(days=1)
            is_closed    = period_end < today

            period = FiscalPeriod(
                fiscal_year=year,
                period_number=month,
                name=period_date.strftime("%b %Y"),
                start_date=period_date,
                end_date=period_end,
                status="closed" if is_closed else "open",
            )
            db.add(period)
            periods.append(period)
    await db.flush()

    # ── Journals ───────────────────────────────────────────────────────────────
    jnl_counter = 1
    expense_accounts = ["6100","6200","6210","6300","6400","6500","6600","6700","6800"]

    for period in periods:
        if period.status != "closed":
            continue

        # Monthly payroll journal
        payroll_total = Decimal(str(round(random.uniform(80000, 120000), 2)))
        jnl = Journal(
            journal_number=f"JNL-{jnl_counter:06d}",
            fiscal_period_id=period.id,
            journal_date=period.end_date,
            description=f"Payroll journal — {period.name}",
            source=JournalSource.PAYROLL,
            status="posted",
            currency="GBP",
            total_debit=payroll_total,
            total_credit=payroll_total,
            is_balanced=True,
        )
        db.add(jnl)
        await db.flush()

        db.add(JournalLine(journal_id=jnl.id, account_code="6100", debit=payroll_total, credit=Decimal("0"), description="Basic pay"))
        db.add(JournalLine(journal_id=jnl.id, account_code="2100", debit=Decimal("0"), credit=payroll_total * Decimal("0.20"), description="PAYE payable"))
        db.add(JournalLine(journal_id=jnl.id, account_code="2110", debit=Decimal("0"), credit=payroll_total * Decimal("0.12"), description="NI payable"))
        db.add(JournalLine(journal_id=jnl.id, account_code="1100", debit=Decimal("0"), credit=payroll_total * Decimal("0.68"), description="Bank payment"))
        jnl_counter += 1

        # Monthly expense journal
        exp_total = Decimal(str(round(random.uniform(5000, 25000), 2)))
        jnl2 = Journal(
            journal_number=f"JNL-{jnl_counter:06d}",
            fiscal_period_id=period.id,
            journal_date=period.end_date,
            description=f"Operating expenses — {period.name}",
            source=JournalSource.AP,
            status="posted",
            currency="GBP",
            total_debit=exp_total,
            total_credit=exp_total,
            is_balanced=True,
        )
        db.add(jnl2)
        await db.flush()

        acc = random.choice(expense_accounts)
        db.add(JournalLine(journal_id=jnl2.id, account_code=acc,    debit=exp_total,      credit=Decimal("0"), description="Operating expense"))
        db.add(JournalLine(journal_id=jnl2.id, account_code="2200", debit=Decimal("0"),   credit=exp_total,    description="AP payable"))
        jnl_counter += 1

    # ── Budgets ────────────────────────────────────────────────────────────────
    budget_accounts = ["6100","6200","6300","6400","6500","6600","6700","6800"]
    budget_count = 0

    for period in periods:
        for acc_code in budget_accounts:
            db.add(Budget(
                fiscal_year=period.fiscal_year,
                period_number=period.period_number,
                account_code=acc_code,
                budgeted_amount=Decimal(str(round(random.uniform(5000, 50000), 2))),
                actual_amount=Decimal(str(round(random.uniform(4000, 55000), 2))),
                currency="GBP",
            ))
            budget_count += 1

    await db.commit()
    print(f"  Created {len(periods)} fiscal periods, {jnl_counter-1} journals, {budget_count} budget entries")
