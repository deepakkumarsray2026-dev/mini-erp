"""
Master seed orchestrator.
Run: python -m app.data.seed_all
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../"))

from app.core.database import AsyncSessionLocal
from app.data import seed_rbac, seed_hcm, seed_payroll, seed_ap, seed_expenses, seed_gl


async def main():
    print("=" * 50)
    print("  Mini-ERP Seed Data Generator")
    print("=" * 50)

    async with AsyncSessionLocal() as db:
        # Order matters — respect foreign key dependencies
        await seed_rbac.run(db)
        hcm_data = await seed_hcm.run(db)
        await seed_payroll.run(db, hcm_data["employees"])
        await seed_ap.run(db)
        await seed_expenses.run(db, hcm_data["employees"])
        await seed_gl.run(db)

    print("=" * 50)
    print("  All seed data created successfully")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
