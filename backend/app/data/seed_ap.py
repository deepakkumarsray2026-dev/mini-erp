"""
Seed AP — 50 vendors, 1000 invoices.
Embedded patterns:
  - 5% duplicate invoices (same vendor + amount + date)
  - Invoice categories for classifier training
  - Vendor risk scores
"""
import random
from datetime import date, timedelta
from decimal import Decimal
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.ap import Vendor, Invoice, InvoiceLine, VendorStatus, InvoiceStatus

fake = Faker("en_GB")
random.seed(42)
Faker.seed(42)

CATEGORIES = ["IT Services", "Office Supplies", "Utilities", "Professional Services",
              "Marketing", "Travel", "Maintenance", "Software Licenses", "Hardware", "Consulting"]

VENDOR_NAMES = [
    "TechVision Ltd", "OfficeWorld UK", "CloudServ Solutions", "BritConsult Partners",
    "GlobalSoft Inc", "ProMaint Services", "DataEdge Analytics", "SwiftSupply Co",
    "LegalEagle LLP", "MediaMax Group", "NetSecure Systems", "FacilityPro UK",
    "TravelEase Corporate", "MarketBoost Agency", "SoftwarePlus Ltd", "HardwareHub",
    "ConsultX Partners", "UtilityFirst", "LogisticsOne", "PrintCraft UK",
    "CyberShield Security", "GreenEnergy Solutions", "HR Dynamics", "FinanceFirst Ltd",
    "DevOps Masters", "CloudInfra UK", "DataVault Systems", "SmartOffice",
    "RapidRepair Services", "WebCraft Studios", "MobileFirst Ltd", "AI Innovations",
    "BlockChain Services", "IoT Solutions UK", "QuantumTech Ltd", "NanoSoft",
    "MacroAnalytics", "PrimeConsulting", "EliteStaffing", "BrandForge",
    "ContentKing", "SEO Masters UK", "PayrollPro Services", "ComplianceFirst",
    "RiskGuard Ltd", "AuditExpert UK", "TaxSavers Partners", "InsuranceLink",
    "PensionPro UK", "BenefitsMax Ltd",
]


async def run(db: AsyncSession) -> list:
    print("Seeding AP...")

    result = await db.execute(select(func.count()).select_from(Vendor))
    if result.scalar() > 0:
        print("  AP already seeded — skipping")
        result = await db.execute(select(Invoice))
        return result.scalars().all()

    # ── Vendors ───────────────────────────────────────────────────────────────
    vendors = []
    for i, name in enumerate(VENDOR_NAMES):
        risk = random.random()
        vendor = Vendor(
            vendor_id=f"VND-{i+1:05d}",
            name=name,
            legal_name=name,
            email=f"accounts@{name.lower().replace(' ', '')[:20]}.com",
            phone=fake.phone_number()[:20],
            address_line1=fake.street_address(),
            city=fake.city(),
            country="GB",
            payment_terms_days=random.choice([14, 30, 45, 60]),
            bank_account=fake.bban(),
            bank_sort_code=f"{random.randint(10,99)}-{random.randint(10,99)}-{random.randint(10,99)}",
            status=VendorStatus.ACTIVE if risk < 0.85 else VendorStatus.BLOCKED,
            risk_score=Decimal(str(round(risk, 4))),
        )
        db.add(vendor)
        vendors.append(vendor)
    await db.flush()
    print(f"  Created {len(vendors)} vendors")

    # ── Invoices ──────────────────────────────────────────────────────────────
    invoices = []
    inv_counter = 1
    today = date.today()
    duplicates_to_create = []

    for i in range(950):
        vendor = random.choice(vendors)
        category = random.choice(CATEGORIES)
        inv_date = today - timedelta(days=random.randint(1, 365 * 3))
        due_date = inv_date + timedelta(days=vendor.payment_terms_days)

        subtotal   = Decimal(str(round(random.uniform(100, 50000), 2)))
        tax_rate   = Decimal("0.20") if random.random() < 0.8 else Decimal("0")
        tax_amount = (subtotal * tax_rate).quantize(Decimal("0.01"))
        total      = subtotal + tax_amount

        days_old = (today - inv_date).days
        if days_old > 90:
            status = random.choice([InvoiceStatus.PAID] * 6 + [InvoiceStatus.POSTED, InvoiceStatus.APPROVED])
        elif days_old > 30:
            status = random.choice([InvoiceStatus.APPROVED, InvoiceStatus.MATCHED, InvoiceStatus.POSTED])
        else:
            status = random.choice([InvoiceStatus.DRAFT, InvoiceStatus.SUBMITTED, InvoiceStatus.UNDER_REVIEW])

        inv = Invoice(
            invoice_number=f"INV-{inv_counter:06d}",
            vendor_id=vendor.id,
            invoice_date=inv_date,
            due_date=due_date,
            received_date=inv_date + timedelta(days=random.randint(0, 5)),
            currency="GBP",
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total,
            status=status,
            description=f"{category} services",
            category=category,
            is_duplicate=False,
        )
        db.add(inv)
        invoices.append(inv)
        inv_counter += 1

        # Mark 5% for duplication
        if random.random() < 0.05:
            duplicates_to_create.append(inv)

    await db.flush()

    # ── Invoice lines ─────────────────────────────────────────────────────────
    for inv in invoices:
        num_lines = random.randint(1, 5)
        remaining = inv.subtotal
        for line_num in range(1, num_lines + 1):
            if line_num == num_lines:
                amount = remaining
            else:
                amount = (remaining * Decimal(str(round(random.uniform(0.1, 0.6), 2)))).quantize(Decimal("0.01"))
                remaining -= amount
            qty = Decimal(str(random.randint(1, 20)))
            unit_price = (amount / qty).quantize(Decimal("0.0001"))
            db.add(InvoiceLine(
                invoice_id=inv.id,
                line_number=line_num,
                description=fake.bs(),
                quantity=qty,
                unit_price=unit_price,
                amount=amount,
                tax_rate=Decimal("0.20"),
            ))

    # ── Duplicate invoices ────────────────────────────────────────────────────
    dup_count = 0
    for orig in duplicates_to_create:
        dup = Invoice(
            invoice_number=f"INV-{inv_counter:06d}",
            vendor_id=orig.vendor_id,
            invoice_date=orig.invoice_date,
            due_date=orig.due_date,
            currency=orig.currency,
            subtotal=orig.subtotal,
            tax_amount=orig.tax_amount,
            total_amount=orig.total_amount,
            status=InvoiceStatus.SUBMITTED,
            description=orig.description,
            category=orig.category,
            is_duplicate=True,
            duplicate_of_id=orig.id,
        )
        db.add(dup)
        inv_counter += 1
        dup_count += 1

    await db.commit()
    print(f"  Created {inv_counter-1} invoices ({dup_count} duplicates) for {len(vendors)} vendors")
    return invoices
