"""
Admin API  —  Roles, Permissions, System health
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import require_permission, ModuleName, Action
from app.models.auth import Role, Permission, UserRole
from app.models.hcm import Employee
from app.models.payroll import PaySlip
from app.models.ap import Invoice
from app.models.expenses import ExpenseReport
from app.schemas.common import MessageResponse

router = APIRouter()


# ── Roles ─────────────────────────────────────────────────────────────────────

@router.get("/roles")
async def list_roles(
    _=Depends(require_permission(ModuleName.ADMIN, Action.READ)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Role).where(Role.is_active == True).order_by(Role.name))
    roles = result.scalars().all()
    return [
        {
            "id":          r.id,
            "code":        r.code,
            "name":        r.name,
            "description": r.description,
            "permissions": [
                {"module": p.module, "action": p.action, "scope": p.scope}
                for p in r.permissions
            ],
        }
        for r in roles
    ]


@router.post("/roles/{role_id}/assign/{user_id}", response_model=MessageResponse)
async def assign_role(
    role_id: str,
    user_id: str,
    _=Depends(require_permission(ModuleName.ADMIN, Action.UPDATE)),
    db: AsyncSession = Depends(get_db),
):
    from app.models.auth import User
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")

    role_result = await db.execute(select(Role).where(Role.id == role_id))
    role = role_result.scalar_one_or_none()
    if not role:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Role not found")

    # Check not already assigned
    existing = await db.execute(
        select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id, UserRole.is_active == True)
    )
    if existing.scalar_one_or_none():
        return {"message": "Role already assigned"}

    user_role = UserRole(user_id=user_id, role_id=role_id, is_active=True)
    db.add(user_role)
    return {"message": f"Role '{role.code}' assigned to user"}


@router.delete("/roles/{role_id}/revoke/{user_id}", response_model=MessageResponse)
async def revoke_role(
    role_id: str,
    user_id: str,
    _=Depends(require_permission(ModuleName.ADMIN, Action.UPDATE)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id, UserRole.is_active == True)
    )
    user_role = result.scalar_one_or_none()
    if not user_role:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Role assignment not found")
    user_role.is_active = False
    return {"message": "Role revoked"}


# ── Dashboard Stats ───────────────────────────────────────────────────────────

@router.get("/stats")
async def get_dashboard_stats(
    _=Depends(require_permission(ModuleName.ADMIN, Action.READ)),
    db: AsyncSession = Depends(get_db),
):
    employee_count = (await db.execute(select(func.count(Employee.id)).where(Employee.is_active == True))).scalar()
    invoice_count  = (await db.execute(select(func.count(Invoice.id)))).scalar()
    expense_count  = (await db.execute(select(func.count(ExpenseReport.id)))).scalar()
    payslip_count  = (await db.execute(select(func.count(PaySlip.id)))).scalar()

    pending_invoices  = (await db.execute(
        select(func.count(Invoice.id)).where(Invoice.status.in_(["submitted", "under_review"]))
    )).scalar()
    pending_expenses  = (await db.execute(
        select(func.count(ExpenseReport.id)).where(ExpenseReport.status.in_(["submitted", "under_review"]))
    )).scalar()
    flagged_expenses  = (await db.execute(
        select(func.count(ExpenseReport.id)).where(ExpenseReport.is_flagged == True)
    )).scalar()

    return {
        "employees":        employee_count,
        "invoices":         invoice_count,
        "expense_reports":  expense_count,
        "payslips":         payslip_count,
        "pending_invoices": pending_invoices,
        "pending_expenses": pending_expenses,
        "flagged_expenses": flagged_expenses,
    }
