"""
Seed RBAC — roles, permissions and default users.
Idempotent — safe to run multiple times.
"""
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.auth import (
    User, Role, RolePermission, UserRole,
    ModuleName, Action, AccessScope,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

M = ModuleName
A = Action
S = AccessScope

ALL_ACTIONS  = [A.CREATE, A.READ, A.UPDATE, A.DELETE, A.APPROVE, A.RUN, A.EXPORT]
READ_ONLY    = [A.READ, A.EXPORT]
FULL_NO_RUN  = [A.CREATE, A.READ, A.UPDATE, A.DELETE, A.APPROVE, A.EXPORT]

ROLES = {
    "platform_admin":    {"name": "Platform administrator",  "description": "Full access to everything",                          "is_system_role": True},
    "hr_superadmin":     {"name": "HR superadmin",           "description": "Full HCM + Payroll. Read Finance.",                  "is_system_role": True},
    "finance_superadmin":{"name": "Finance superadmin",      "description": "Full Finance modules. Read HCM.",                    "is_system_role": True},
    "workforce_user":    {"name": "Workforce user",          "description": "Full Workforce module only",                         "is_system_role": False},
    "payroll_user":      {"name": "Payroll user",            "description": "Full Payroll. Read Workforce + GL.",                 "is_system_role": False},
    "ap_user":           {"name": "Accounts payable user",   "description": "Full AP. Read Procurement + GL.",                   "is_system_role": False},
    "expenses_user":     {"name": "Expenses user",           "description": "Own expense reports only.",                          "is_system_role": False},
    "procurement_user":  {"name": "Procurement user",        "description": "Full Procurement. Read AP.",                         "is_system_role": False},
    "gl_user":           {"name": "General ledger user",     "description": "Full GL. Read AP.",                                  "is_system_role": False},
}

ROLE_PERMISSIONS = {
    "platform_admin":     [(M.WORKFORCE, ALL_ACTIONS, S.ALL), (M.PAYROLL, ALL_ACTIONS, S.ALL), (M.AP, ALL_ACTIONS, S.ALL), (M.EXPENSES, ALL_ACTIONS, S.ALL), (M.PROCUREMENT, ALL_ACTIONS, S.ALL), (M.GL, ALL_ACTIONS, S.ALL), (M.AI, ALL_ACTIONS, S.ALL), (M.ADMIN, ALL_ACTIONS, S.ALL)],
    "hr_superadmin":      [(M.WORKFORCE, ALL_ACTIONS, S.ALL), (M.PAYROLL, ALL_ACTIONS, S.ALL), (M.EXPENSES, READ_ONLY, S.ALL), (M.GL, READ_ONLY, S.ALL), (M.AI, FULL_NO_RUN, S.ALL)],
    "finance_superadmin": [(M.WORKFORCE, READ_ONLY, S.ALL), (M.PAYROLL, READ_ONLY, S.ALL), (M.AP, ALL_ACTIONS, S.ALL), (M.EXPENSES, ALL_ACTIONS, S.ALL), (M.PROCUREMENT, ALL_ACTIONS, S.ALL), (M.GL, ALL_ACTIONS, S.ALL), (M.AI, FULL_NO_RUN, S.ALL)],
    "workforce_user":     [(M.WORKFORCE, FULL_NO_RUN, S.ALL), (M.AI, [A.READ], S.ALL)],
    "payroll_user":       [(M.WORKFORCE, READ_ONLY, S.ALL), (M.PAYROLL, ALL_ACTIONS, S.ALL), (M.GL, READ_ONLY, S.ALL), (M.AI, [A.READ], S.ALL)],
    "ap_user":            [(M.AP, FULL_NO_RUN, S.ALL), (M.PROCUREMENT, READ_ONLY, S.ALL), (M.GL, READ_ONLY, S.ALL), (M.AI, [A.READ], S.ALL)],
    "expenses_user":      [(M.EXPENSES, FULL_NO_RUN, S.OWN), (M.AI, [A.READ], S.OWN)],
    "procurement_user":   [(M.PROCUREMENT, FULL_NO_RUN, S.ALL), (M.AP, READ_ONLY, S.ALL), (M.AI, [A.READ], S.ALL)],
    "gl_user":            [(M.GL, ALL_ACTIONS, S.ALL), (M.AP, READ_ONLY, S.ALL), (M.AI, [A.READ], S.ALL)],
}

DEMO_USERS = [
    {"username": "platform_admin",     "email": "admin@mini-erp.local",          "full_name": "Platform Admin",      "role": "platform_admin",     "password": "Admin@123!"},
    {"username": "hr_admin",           "email": "hr.admin@mini-erp.local",        "full_name": "Sarah HR Admin",      "role": "hr_superadmin",      "password": "Admin@123!"},
    {"username": "finance_admin",      "email": "fin.admin@mini-erp.local",       "full_name": "James Finance Admin", "role": "finance_superadmin", "password": "Admin@123!"},
    {"username": "workforce_user1",    "email": "workforce1@mini-erp.local",      "full_name": "Alice Workforce",     "role": "workforce_user",     "password": "User@123!"},
    {"username": "payroll_user1",      "email": "payroll1@mini-erp.local",        "full_name": "Bob Payroll",         "role": "payroll_user",       "password": "User@123!"},
    {"username": "ap_user1",           "email": "ap1@mini-erp.local",             "full_name": "Carol AP",            "role": "ap_user",            "password": "User@123!"},
    {"username": "expenses_user1",     "email": "expenses1@mini-erp.local",       "full_name": "Dave Expenses",       "role": "expenses_user",      "password": "User@123!"},
    {"username": "procurement_user1",  "email": "procurement1@mini-erp.local",    "full_name": "Eve Procurement",     "role": "procurement_user",   "password": "User@123!"},
    {"username": "gl_user1",           "email": "gl1@mini-erp.local",             "full_name": "Frank GL",            "role": "gl_user",            "password": "User@123!"},
]


async def seed_roles(db: AsyncSession) -> dict[str, Role]:
    """Upsert all roles. Returns dict of code → Role."""
    roles = {}
    for code, data in ROLES.items():
        result = await db.execute(select(Role).where(Role.code == code))
        role = result.scalar_one_or_none()
        if not role:
            role = Role(code=code, **data)
            db.add(role)
            await db.flush()
            print(f"  Created role: {code}")
        roles[code] = role
    return roles


async def seed_permissions(db: AsyncSession, roles: dict[str, Role]) -> None:
    """Upsert all permissions for each role."""
    for role_code, perms in ROLE_PERMISSIONS.items():
        role = roles[role_code]
        for module, actions, scope in perms:
            for action in actions:
                result = await db.execute(
                    select(RolePermission).where(
                        RolePermission.role_id == role.id,
                        RolePermission.module == module,
                        RolePermission.action == action,
                    )
                )
                perm = result.scalar_one_or_none()
                if not perm:
                    db.add(RolePermission(
                        role_id=role.id,
                        module=module,
                        action=action,
                        scope=scope,
                    ))


async def seed_users(db: AsyncSession, roles: dict[str, Role]) -> None:
    """Create demo users with role assignments."""
    for u in DEMO_USERS:
        result = await db.execute(select(User).where(User.username == u["username"]))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                username=u["username"],
                email=u["email"],
                full_name=u["full_name"],
                hashed_password=pwd_context.hash(u["password"]),
                is_active=True,
                is_verified=True,
                must_change_password=False,
            )
            db.add(user)
            await db.flush()
            db.add(UserRole(user_id=user.id, role_id=roles[u["role"]].id))
            print(f"  Created user: {u['username']} → {u['role']}")


async def run(db: AsyncSession) -> None:
    print("Seeding RBAC...")
    roles = await seed_roles(db)
    await seed_permissions(db, roles)
    await seed_users(db, roles)
    await db.commit()
    print("RBAC seed complete.")
