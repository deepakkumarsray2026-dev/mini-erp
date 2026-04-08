"""
Master seed orchestrator.
Run: python -m app.data.seed_all
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../"))

from app.core.database import AsyncSessionLocal
from app.data import seed_rbac, seed_hcm, seed_payroll, seed_ap, seed_expenses, seed_gl, seed_procurement


async def main():
    print("=" * 50)
    print("  Mini-ERP Seed Data Generator")
    print("=" * 50)

    async with AsyncSessionLocal() as db:
        # Order matters — respect foreign key dependencies
        print("[1/7] Seeding RBAC ...")
        await seed_rbac.run(db)

        print("[2/7] Seeding HCM ...")
        hcm_data = await seed_hcm.run(db)

        print("[3/7] Seeding Payroll ...")
        await seed_payroll.run(db, hcm_data["employees"])

        print("[4/7] Seeding AP (Vendors + Invoices) ...")
        await seed_ap.run(db)

        print("[5/7] Seeding Expenses ...")
        await seed_expenses.run(db, hcm_data["employees"])

        print("[6/7] Seeding GL ...")
        await seed_gl.run(db)

        print("[7/7] Seeding Procurement ...")
        await seed_procurement.seed_procurement(db)

        await db.commit()

    print("=" * 50)
    print("  All seed data created successfully ✓")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
