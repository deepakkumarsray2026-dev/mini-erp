"""
Auth API — login, logout, token refresh, password change,
user management (admin only).
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import (
    get_current_user, require_role, ModuleName, Action, require_permission,
)
from app.schemas.auth import (
    LoginRequest, TokenResponse, RefreshRequest,
    ChangePasswordRequest, UserResponse, UserCreate,
    UserUpdate, UserListResponse,
)
from app.schemas.common import PaginatedResponse, MessageResponse, paginate
from app.services import auth_service
from app.models.auth import User

router = APIRouter()


# ── Public endpoints ──────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse, summary="Login")
async def login(
    data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    result = await auth_service.login(db, data)
    return result


@router.post("/refresh", response_model=TokenResponse, summary="Refresh token")
async def refresh(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    return await auth_service.refresh_access_token(db, data.refresh_token)


@router.post("/logout", response_model=MessageResponse, summary="Logout")
async def logout(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    await auth_service.logout(db, data.refresh_token)
    return {"message": "Logged out successfully"}


# ── Authenticated endpoints ───────────────────────────────────────────────────

@router.get("/me", response_model=UserResponse, summary="Get current user")
async def get_me(current_user: User = Depends(get_current_user)):
    role_codes = [ur.role.code for ur in current_user.user_roles if ur.is_active]
    permissions = []
    for ur in current_user.user_roles:
        if ur.is_active:
            for perm in ur.role.permissions:
                permissions.append(perm)

    return {
        "id":                   current_user.id,
        "username":             current_user.username,
        "email":                current_user.email,
        "full_name":            current_user.full_name,
        "is_active":            current_user.is_active,
        "is_verified":          current_user.is_verified,
        "must_change_password": current_user.must_change_password,
        "last_login_at":        current_user.last_login_at,
        "roles":                role_codes,
        "permissions":          permissions,
    }


@router.post("/change-password", response_model=MessageResponse, summary="Change password")
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await auth_service.change_password(
        db, current_user,
        data.current_password,
        data.new_password,
    )
    return {"message": "Password changed successfully"}


# ── Admin — user management ───────────────────────────────────────────────────

@router.get(
    "/users",
    response_model=PaginatedResponse[UserListResponse],
    summary="List users (admin only)",
)
async def list_users(
    page: int = 1,
    page_size: int = 20,
    search: str = "",
    _=Depends(require_permission(ModuleName.ADMIN, Action.READ)),
    db: AsyncSession = Depends(get_db),
):
    users, total = await auth_service.list_users(db, page, page_size, search)
    items = []
    for u in users:
        items.append({
            "id":            u.id,
            "username":      u.username,
            "email":         u.email,
            "full_name":     u.full_name,
            "is_active":     u.is_active,
            "roles":         [ur.role.code for ur in u.user_roles if ur.is_active],
            "last_login_at": u.last_login_at,
        })
    return paginate(items, total, page, page_size)


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=201,
    summary="Create user (admin only)",
)
async def create_user(
    data: UserCreate,
    _=Depends(require_permission(ModuleName.ADMIN, Action.CREATE)),
    db: AsyncSession = Depends(get_db),
):
    return await auth_service.create_user(db, data)


@router.patch(
    "/users/{user_id}",
    response_model=MessageResponse,
    summary="Update user (admin only)",
)
async def update_user(
    user_id: str,
    data: UserUpdate,
    _=Depends(require_permission(ModuleName.ADMIN, Action.UPDATE)),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.email is not None:
        user.email = data.email
    if data.is_active is not None:
        user.is_active = data.is_active
    await db.commit()
    return {"message": "User updated successfully"}
