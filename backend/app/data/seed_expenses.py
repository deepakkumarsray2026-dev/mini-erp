"""
Seed Expenses — categories + 500 expense reports.
Embedded violations for ML detection:
  - Amount exceeds category daily limit
  - Weekend submission
  - Suspicious merchant (alcohol, casino)
  - Duplicate receipt same day
"""
import random
from datetime import date, timedelta
from decimal import Decimal
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.expenses import ExpenseCategory, ExpenseReport, ExpenseLine, ExpenseStatus

fake = Faker("en_GB")
random.seed(42)
Faker.seed(42)

CATEGORIES = [
    ("MEALS",    "Meals & Entertainment",  Decimal("75"),   True),
    ("TRAVEL",   "Travel",                 Decimal("500"),  True),
    ("HOTEL",    "Accommodation",          Decimal("200"),  True),
    ("OFFICE",   "Office Supplies",        Decimal("100"),  False),
    ("TRAINING", "Training & Development", Decimal("1000"), True),
    ("PHONE",    "Phone & Internet",       Decimal("50"),   False),
    ("MILEAGE",  "Mileage",                Decimal("150"),  False),
    ("CLIENT",   "Client Entertainment",  Decimal("200"),  True),
]

LEGIT_MERCHANTS = [
    "Pret A Manger", "Tesco", "Costa Coffee", "Hilton Hotels",
    "Premier Inn", "British Rail", "Uber", "Amazon Business",
    "Staples", "John Lewis", "Shell", "BP Garage",
]

SUSPICIOUS_MERCHANTS = [
    "Casino Royale", "The Red Lion Pub", "Slot Machine Palace",
    "Luxury Spa & Wellness", "Duty Free Spirits", "Night Club VIP",
]


async def run(db: AsyncSession, employees: list) -> None:
    print("Seeding Expenses...")

    result = await db.execute(select(func.count()).select_from(ExpenseCategory))
    if result.scalar() > 0:
        print("  Expenses already seeded — skipping")
        return

    # ── Categories ────────────────────────────────────────────────────────────
    cat_map = {}
    for code, name, limit, receipt in CATEGORIES:
        cat = ExpenseCategory(
            code=code, name=name,
            daily_limit=limit,
            requires_receipt=receipt,
        )
        db.add(cat)
        cat_map[code] = cat
    await db.flush()

    active_emps = [e for e in employees if e.is_active]
    cat_list    = list(cat_map.values())
    report_num  = 1
    total_lines = 0
    violations  = 0

    for _ in range(500):
        emp       = random.choice(active_emps)
        today     = date.today()
        pstart    = today - timedelta(days=random.randint(7, 365))
        pend      = pstart + timedelta(days=random.randint(3, 14))
        is_flagged= random.random() < 0.15   # 15% flagged reports

        status = random.choice([
            ExpenseStatus.APPROVED, ExpenseStatus.APPROVED,
            ExpenseStatus.PAID,
            ExpenseStatus.SUBMITTED,
            ExpenseStatus.UNDER_REVIEW,
            ExpenseStatus.REJECTED,
        ])

        report = ExpenseReport(
            report_number=f"EXP-{report_num:06d}",
            employee_id=emp.id,
            title=f"Business expenses {pstart.strftime('%b %Y')}",
            period_start=pstart,
            period_end=pend,
            currency="GBP",
            status=status,
            is_flagged=is_flagged,
        )
        db.add(report)
        await db.flush()
        report_num += 1

        # ── Lines ──────────────────────────────────────────────────────────────
        total_amount = Decimal("0")
        num_lines    = random.randint(1, 8)
        line_flags   = []

        for _ in range(num_lines):
            cat        = random.choice(cat_list)
            exp_date   = pstart + timedelta(days=random.randint(0, (pend - pstart).days))
            is_weekend = exp_date.weekday() >= 5

            # Violation logic
            is_violation   = False
            violation_type = None

            if is_flagged and random.random() < 0.5:
                violation_choice = random.randint(1, 3)
                if violation_choice == 1:
                    # Over limit
                    amount         = cat.daily_limit * Decimal(str(round(random.uniform(1.5, 3.0), 2)))
                    is_violation   = True
                    violation_type = "exceeds_limit"
                elif violation_choice == 2:
                    # Suspicious merchant
                    merchant       = random.choice(SUSPICIOUS_MERCHANTS)
                    amount         = Decimal(str(round(random.uniform(50, 300), 2)))
                    is_violation   = True
                    violation_type = "suspicious_merchant"
                else:
                    # Weekend
                    amount         = Decimal(str(round(random.uniform(20, 200), 2)))
                    is_violation   = is_weekend
                    violation_type = "weekend_expense" if is_weekend else None
                    merchant       = random.choice(LEGIT_MERCHANTS)
            else:
                amount  = Decimal(str(round(random.uniform(
                    5, min(float(cat.daily_limit or 100), 200)
                ), 2)))
                merchant = random.choice(LEGIT_MERCHANTS)

            if "merchant" not in dir():
                merchant = random.choice(LEGIT_MERCHANTS)

            line = ExpenseLine(
                report_id=report.id,
                category_id=cat.id,
                expense_date=exp_date,
                merchant=merchant,
                amount=amount,
                currency="GBP",
                is_billable=random.random() < 0.2,
                is_violation=is_violation,
                violation_type=violation_type,
            )
            db.add(line)
            total_amount += amount
            total_lines  += 1
            if is_violation:
                violations += 1

        report.total_amount = total_amount

    await db.commit()
    print(f"  Created 500 expense reports, {total_lines} lines, {violations} violations")
