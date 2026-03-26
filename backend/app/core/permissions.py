import enum
from datetime import datetime, timezone
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_token

security = HTTPBearer()


class ModuleName(str, enum.Enum):
    WORKFORCE    = "workforce"
    PAYROLL      = "payroll"
    AP           = "accounts_payable"
    EXPENSES     = "expenses"
    PROCUREMENT  = "procurement"
    GL           = "general_ledger"
    AI           = "ai"
    ADMIN        = "admin"


class Action(str, enum.Enum):
    CREATE  = "create"
    READ    = "read"
    UPDATE  = "update"
    DELETE  = "delete"
    APPROVE = "approve"
    RUN     = "run"
    EXPORT  = "export"


class AccessScope(str, enum.Enum):
    ALL  = "all"
    OWN  = "own"
    DEPT = "dept"


class PermissionContext:
    def __init__(self, user, scope: AccessScope):
        self.user = user
        self.scope = scope

    @property
    def is_own_scope(self) -> bool:
        return self.scope == AccessScope.OWN

    @property
    def employee_id(self) -> str | None:
        return getattr(self.user, "employee_id", None)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: AsyncSession = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(credentials.credentials)
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        if not user_id or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Import here to avoid circular imports
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.auth import User, UserRole, Role

    result = await db.execute(
        select(User)
        .where(User.id == user_id, User.is_active == True)
        .options(
            selectinload(User.user_roles)
            .selectinload(UserRole.role)
            .selectinload(Role.permissions)
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise credentials_exception
    return user


CurrentUser = Annotated[object, Depends(get_current_user)]


def require_permission(module: ModuleName, action: Action):
    async def checker(
        current_user=Depends(get_current_user),
    ) -> PermissionContext:
        from app.models.auth import AccessScope as ModelScope
        now = datetime.now(timezone.utc)

        for user_role in current_user.user_roles:
            if not user_role.is_active:
                continue
            if user_role.valid_from and now < user_role.valid_from:
                continue
            if user_role.valid_until and now > user_role.valid_until:
                continue
            for perm in user_role.role.permissions:
                if perm.module == module and perm.action == action:
                    return PermissionContext(
                        user=current_user,
                        scope=AccessScope(perm.scope.value)
                    )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: {action.value} on {module.value}",
        )
    return checker


# Convenience shortcuts
def can_read(module: ModuleName):
    return require_permission(module, Action.READ)

def can_create(module: ModuleName):
    return require_permission(module, Action.CREATE)

def can_update(module: ModuleName):
    return require_permission(module, Action.UPDATE)

def can_delete(module: ModuleName):
    return require_permission(module, Action.DELETE)

def can_approve(module: ModuleName):
    return require_permission(module, Action.APPROVE)

def can_run(module: ModuleName):
    return require_permission(module, Action.RUN)

def can_export(module: ModuleName):
    return require_permission(module, Action.EXPORT)
