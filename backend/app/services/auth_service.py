"""
Auth service — login, token management, user CRUD.
"""
import hashlib
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from loguru import logger

from app.models.auth import User, Role, UserRole, RefreshToken
from app.core.security import (
    verify_password, hash_password,
    create_access_token, create_refresh_token, decode_token,
)
from app.core.config import settings
from app.schemas.auth import LoginRequest, UserCreate


MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES     = 15


async def get_user_with_roles(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.user_roles)
            .selectinload(UserRole.role)
            .selectinload(Role.permissions)
        )
    )
    return result.scalar_one_or_none()


async def login(db: AsyncSession, data: LoginRequest) -> dict:
    # Find user by username or email
    result = await db.execute(
        select(User)
        .where(
            (User.username == data.username) |
            (User.email == data.username)
        )
        .options(
            selectinload(User.user_roles)
            .selectinload(UserRole.role)
            .selectinload(Role.permissions)
        )
    )
    user = result.scalar_one_or_none()

    # User not found
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Account locked
    if user.locked_until and datetime.now(timezone.utc) < user.locked_until:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account locked. Try again after {user.locked_until.strftime('%H:%M UTC')}",
        )

    # Wrong password
    if not verify_password(data.password, user.hashed_password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)
            logger.warning(f"Account locked after {MAX_FAILED_ATTEMPTS} failed attempts: {user.username}")
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Inactive
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    # Success — reset failed attempts
    user.failed_login_attempts = 0
    user.locked_until          = None
    user.last_login_at         = datetime.now(timezone.utc)

    # Build tokens
    role_codes   = [ur.role.code for ur in user.user_roles if ur.is_active]
    access_token = create_access_token(user.id, role_codes)
    refresh_token_raw = create_refresh_token(user.id)

    # Store refresh token hash
    token_hash = hashlib.sha256(refresh_token_raw.encode()).hexdigest()
    db_token = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(db_token)
    await db.commit()

    logger.info(f"Login success: {user.username}")

    return {
        "access_token":  access_token,
        "refresh_token": refresh_token_raw,
        "token_type":    "bearer",
        "expires_in":    settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user":          user,
    }


async def refresh_access_token(db: AsyncSession, refresh_token: str) -> dict:
    try:
        payload = decode_token(refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    db_token = result.scalar_one_or_none()

    if not db_token or not db_token.is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired or revoked",
        )

    user = await get_user_with_roles(db, payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    role_codes    = [ur.role.code for ur in user.user_roles if ur.is_active]
    new_access    = create_access_token(user.id, role_codes)
    new_refresh   = create_refresh_token(user.id)
    new_hash      = hashlib.sha256(new_refresh.encode()).hexdigest()

    # Revoke old, issue new
    db_token.revoked_at = datetime.now(timezone.utc)
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=new_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    ))
    await db.commit()

    return {
        "access_token":  new_access,
        "refresh_token": new_refresh,
        "token_type":    "bearer",
        "expires_in":    settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user":          user,
    }


async def logout(db: AsyncSession, refresh_token: str) -> None:
    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    db_token = result.scalar_one_or_none()
    if db_token:
        db_token.revoked_at = datetime.now(timezone.utc)
        await db.commit()


async def change_password(
    db: AsyncSession,
    user: User,
    current_password: str,
    new_password: str,
) -> None:
    if not verify_password(current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    user.hashed_password      = hash_password(new_password)
    user.must_change_password = False
    user.password_changed_at  = datetime.now(timezone.utc)
    await db.commit()


async def create_user(db: AsyncSession, data: UserCreate) -> User:
    # Check username/email uniqueness
    result = await db.execute(
        select(User).where(
            (User.username == data.username) | (User.email == data.email)
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists",
        )

    # Get role
    role_result = await db.execute(
        select(Role).where(Role.code == data.role_code)
    )
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role '{data.role_code}' not found",
        )

    user = User(
        username=data.username,
        email=data.email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        employee_id=data.employee_id,
        is_active=True,
        is_verified=True,
        must_change_password=True,
    )
    db.add(user)
    await db.flush()
    db.add(UserRole(user_id=user.id, role_id=role.id))
    await db.commit()
    return user


async def list_users(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    search: str = "",
) -> tuple[list[User], int]:
    from sqlalchemy import func, or_

    query = select(User).options(
        selectinload(User.user_roles).selectinload(UserRole.role)
    )
    if search:
        query = query.where(
            or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%"),
            )
        )

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar()

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return result.scalars().all(), total
