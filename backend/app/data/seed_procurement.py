"""
Seed Procurement — purchase requisitions, purchase orders, goods receipts.
Depends on: seed_hcm (employees/departments), seed_ap (vendors).
"""
import random
from datetime import date, timedelta
from decimal import Decimal
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.procurement import PurchaseRequisition, PurchaseOrder, POLine, GoodsReceipt
from app.models.hcm import Employee, Department
from app.models.ap import Vendor

fake = Faker("en_GB")
random.seed(42)
Faker.seed(42)

ITEMS = [
    ("LAPTOP-001",  "Dell Latitude Laptop 14\"",        Decimal("899.00")),
    ("MONITOR-001", "27\" 4K Monitor",                  Decimal("349.00")),
    ("CHAIR-001",   "Ergonomic Office Chair",            Decimal("249.00")),
    ("SW-001",      "Microsoft 365 Annual License",      Decimal("99.00")),
    ("PAPER-001",   "A4 Copy Paper (Box of 5 Reams)",    Decimal("24.99")),
    ("HEADSET-001", "Noise-cancelling Headset",          Decimal("149.00")),
    ("DESK-001",    "Sit-stand Desk",                    Decimal("599.00")),
    ("SERVER-001",  "Rack Server Unit",                  Decimal("2499.00")),
    ("CAB-001",     "Cat6 Network Cable (100m)",         Decimal("39.99")),
    ("PHONE-001",   "IP Desk Phone",                     Decimal("89.00")),
]

PR_STATUSES = ["draft", "submitted", "approved", "rejected"]
PO_STATUSES = ["draft", "issued", "partial", "closed"]


async def seed_procurement(session: AsyncSession) -> None:
    # Fetch employees and vendors
    employees = (await session.execute(select(Employee).where(Employee.is_active == True))).scalars().all()
    vendors   = (await session.execute(select(Vendor).where(Vendor.is_active == True))).scalars().all()
    depts     = (await session.execute(select(Department))).scalars().all()

    if not employees or not vendors:
        return

    pr_list   = []
    po_list   = []
    pr_count  = 0
    po_count  = 0
    gr_count  = 0

    base_date = date(2024, 1, 1)

    # ── 200 Purchase Requisitions ─────────────────────────────────────────────
    for i in range(200):
        emp     = random.choice(employees)
        dept    = random.choice(depts)
        status  = random.choices(PR_STATUSES, weights=[10, 30, 50, 10])[0]
        req_dt  = base_date + timedelta(days=random.randint(0, 365))
        amount  = Decimal(str(random.randint(100, 5000)))
        pr_count += 1

        pr = PurchaseRequisition(
            pr_number     = f"PR-{pr_count:05d}",
            requested_by  = emp.id,
            department_id = dept.id,
            title         = fake.bs().title(),
            justification = fake.sentence(),
            required_date = req_dt + timedelta(days=random.randint(7, 30)),
            total_amount  = amount,
            currency      = "GBP",
            status        = status,
            approved_by   = random.choice(employees).id if status == "approved" else None,
        )
        session.add(pr)
        pr_list.append((pr, status))

    await session.flush()

    # ── 150 Purchase Orders (from approved PRs or standalone) ─────────────────
    approved_prs = [pr for pr, s in pr_list if s == "approved"]
    for i in range(150):
        vendor      = random.choice(vendors)
        status      = random.choices(PO_STATUSES, weights=[5, 40, 30, 25])[0]
        issued_date = base_date + timedelta(days=random.randint(0, 365))
        pr          = random.choice(approved_prs) if approved_prs and random.random() < 0.6 else None

        item        = random.choice(ITEMS)
        qty         = Decimal(str(random.randint(1, 20)))
        line_amount = (item[2] * qty).quantize(Decimal("0.01"))
        po_count   += 1

        po = PurchaseOrder(
            po_number         = f"PO-{po_count:05d}",
            requisition_id    = pr.id if pr else None,
            vendor_id         = vendor.id,
            issued_date       = issued_date,
            expected_delivery = issued_date + timedelta(days=random.randint(7, 45)),
            total_amount      = line_amount,
            currency          = "GBP",
            status            = status,
            approved_by       = random.choice(employees).id,
            terms             = f"Net {vendor.payment_terms_days}",
        )
        session.add(po)
        await session.flush()  # ensure po.id is populated before using it
        po_list.append((po, status))

        # Add a PO line
        line = POLine(
            po_id          = po.id,
            line_number    = 1,
            item_code      = item[0],
            description    = item[1],
            quantity       = qty,
            unit_of_measure= "EA",
            unit_price     = item[2],
            amount         = line_amount,
        )
        session.add(line)

    await session.flush()

    # ── Goods Receipts for partial/closed POs ─────────────────────────────────
    for po, status in po_list:
        if status in ("partial", "closed"):
            gr_count += 1
            gr = GoodsReceipt(
                receipt_number = f"GR-{gr_count:05d}",
                po_id          = po.id,
                received_by    = random.choice(employees).id,
                receipt_date   = po.issued_date + timedelta(days=random.randint(5, 20)),
                notes          = "Goods received in good condition" if random.random() > 0.1 else "Partial delivery noted",
            )
            session.add(gr)

    await session.flush()
