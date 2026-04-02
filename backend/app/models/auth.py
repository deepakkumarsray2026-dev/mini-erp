import enum
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ModuleName(str, enum.Enum):
    WORKFORCE   = "workforce"
    PAYROLL     = "payroll"
    AP          = "accounts_payable"
    EXPENSES    = "expenses"
    PROCUREMENT = "procurement"
    GL          = "general_ledger"
    AI          = "ai"
    ADMIN       = "admin"


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


class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}

    id:                    Mapped[str]           = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    username:              Mapped[str]           = mapped_column(String(50), unique=True, nullable=False)
    email:                 Mapped[str]           = mapped_column(String(150), unique=True, nullable=False)
    hashed_password:       Mapped[str]           = mapped_column(String(200), nullable=False)
    employee_id:           Mapped[str | None]    = mapped_column(UUID(as_uuid=False), ForeignKey("hcm.employees.id"), nullable=True)
    full_name:             Mapped[str]           = mapped_column(String(120), nullable=False)
    avatar_url:            Mapped[str | None]    = mapped_column(String(500))
    is_active:             Mapped[bool]          = mapped_column(Boolean, default=True, nullable=False)
    is_verified:           Mapped[bool]          = mapped_column(Boolean, default=False, nullable=False)
    must_change_password:  Mapped[bool]          = mapped_column(Boolean, default=True)
    last_login_at:         Mapped[datetime|None] = mapped_column(DateTime(timezone=True))
    last_login_ip:         Mapped[str | None]    = mapped_column(String(45))
    failed_login_attempts: Mapped[int]           = mapped_column(default=0)
    locked_until:          Mapped[datetime|None] = mapped_column(DateTime(timezone=True))

    user_roles:     Mapped[list["UserRole"]]     = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

    @property
    def roles(self) -> list["Role"]:
        return [ur.role for ur in self.user_roles if ur.is_active]


class Role(Base, TimestampMixin):
    __tablename__ = "roles"
    __table_args__ = {"schema": "auth"}

    id:             Mapped[str]      = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    code:           Mapped[str]      = mapped_column(String(50), unique=True, nullable=False)
    name:           Mapped[str]      = mapped_column(String(100), nullable=False)
    description:    Mapped[str|None] = mapped_column(Text)
    is_system_role: Mapped[bool]     = mapped_column(Boolean, default=False)
    is_active:      Mapped[bool]     = mapped_column(Boolean, default=True)

    permissions: Mapped[list["RolePermission"]] = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    user_roles:  Mapped[list["UserRole"]]       = relationship("UserRole", back_populates="role")


class RolePermission(Base, TimestampMixin):
    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "module", "action", name="uq_role_module_action"),
        {"schema": "auth"},
    )

    id:      Mapped[str]         = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    role_id: Mapped[str]         = mapped_column(UUID(as_uuid=False), ForeignKey("auth.roles.id"), nullable=False)
    module:  Mapped[ModuleName]  = mapped_column(Enum(ModuleName), nullable=False)
    action:  Mapped[Action]      = mapped_column(Enum(Action), nullable=False)
    scope:   Mapped[AccessScope] = mapped_column(Enum(AccessScope), default=AccessScope.ALL, nullable=False)

    role: Mapped[Role] = relationship("Role", back_populates="permissions")


class UserRole(Base, TimestampMixin):
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_role"),
        {"schema": "auth"},
    )

    id:          Mapped[str]          = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    user_id:     Mapped[str]          = mapped_column(UUID(as_uuid=False), ForeignKey("auth.users.id"), nullable=False)
    role_id:     Mapped[str]          = mapped_column(UUID(as_uuid=False), ForeignKey("auth.roles.id"), nullable=False)
    assigned_by: Mapped[str | None]   = mapped_column(UUID(as_uuid=False))
    valid_from:  Mapped[datetime|None]= mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime|None]= mapped_column(DateTime(timezone=True))
    is_active:   Mapped[bool]         = mapped_column(Boolean, default=True)

    user: Mapped[User] = relationship("User", back_populates="user_roles")
    role: Mapped[Role] = relationship("Role", back_populates="user_roles")


class RefreshToken(Base, TimestampMixin):
    __tablename__ = "refresh_tokens"
    __table_args__ = {"schema": "auth"}

    id:         Mapped[str]           = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    user_id:    Mapped[str]           = mapped_column(UUID(as_uuid=False), ForeignKey("auth.users.id"), nullable=False)
    token_hash: Mapped[str]           = mapped_column(String(200), unique=True, nullable=False)
    expires_at: Mapped[datetime]      = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True))
    ip_address: Mapped[str | None]    = mapped_column(String(45))
    user_agent: Mapped[str | None]    = mapped_column(String(500))

    user: Mapped[User] = relationship("User", back_populates="refresh_tokens")
