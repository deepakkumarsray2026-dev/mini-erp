import enum
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ExpenseStatus(str, enum.Enum):
    DRAFT        = "draft"
    SUBMITTED    = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED     = "approved"
    REJECTED     = "rejected"
    PAID         = "paid"


class ExpenseCategory(Base, TimestampMixin):
    __tablename__ = "expense_categories"
    __table_args__ = {"schema": "expenses"}

    id:               Mapped[str]          = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    code:             Mapped[str]          = mapped_column(String(20), unique=True, nullable=False)
    name:             Mapped[str]          = mapped_column(String(100), nullable=False)
    daily_limit:      Mapped[Decimal|None] = mapped_column(Numeric(10, 2))
    requires_receipt: Mapped[bool]         = mapped_column(Boolean, default=True)
    gl_account_code:  Mapped[str|None]     = mapped_column(String(20))
    is_active:        Mapped[bool]         = mapped_column(Boolean, default=True)


class ExpenseReport(Base, TimestampMixin):
    __tablename__ = "expense_reports"
    __table_args__ = {"schema": "expenses"}

    id:               Mapped[str]            = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    report_number:    Mapped[str]            = mapped_column(String(30), unique=True, nullable=False)
    employee_id:      Mapped[str]            = mapped_column(UUID(as_uuid=False), ForeignKey("hcm.employees.id"), nullable=False)
    title:            Mapped[str]            = mapped_column(String(200), nullable=False)
    period_start:     Mapped[date]           = mapped_column(Date, nullable=False)
    period_end:       Mapped[date]           = mapped_column(Date, nullable=False)
    total_amount:     Mapped[Decimal]        = mapped_column(Numeric(15, 2), default=0)
    currency:         Mapped[str]            = mapped_column(String(3), default="GBP")
    status:           Mapped[ExpenseStatus]  = mapped_column(Enum(ExpenseStatus), default=ExpenseStatus.DRAFT)
    approved_by:      Mapped[str|None]       = mapped_column(UUID(as_uuid=False))
    rejection_reason: Mapped[str|None]       = mapped_column(Text)
    violation_flags:  Mapped[dict|None]      = mapped_column(JSONB)
    violation_score:  Mapped[float|None]     = mapped_column(Numeric(5, 4))
    is_flagged:       Mapped[bool]           = mapped_column(Boolean, default=False)

    employee: Mapped["Employee"]           = relationship("Employee", back_populates="expense_reports")
    lines:    Mapped[list["ExpenseLine"]]  = relationship("ExpenseLine", back_populates="report", cascade="all, delete-orphan")


class ExpenseLine(Base, TimestampMixin):
    __tablename__ = "expense_lines"
    __table_args__ = {"schema": "expenses"}

    id:             Mapped[str]          = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    report_id:      Mapped[str]          = mapped_column(UUID(as_uuid=False), ForeignKey("expenses.expense_reports.id"), nullable=False)
    category_id:    Mapped[str]          = mapped_column(UUID(as_uuid=False), ForeignKey("expenses.expense_categories.id"), nullable=False)
    expense_date:   Mapped[date]         = mapped_column(Date, nullable=False)
    merchant:       Mapped[str]          = mapped_column(String(200), nullable=False)
    description:    Mapped[str|None]     = mapped_column(Text)
    amount:         Mapped[Decimal]      = mapped_column(Numeric(15, 2), nullable=False)
    currency:       Mapped[str]          = mapped_column(String(3), default="GBP")
    receipt_path:   Mapped[str|None]     = mapped_column(String(500))
    is_billable:    Mapped[bool]         = mapped_column(Boolean, default=False)
    project_code:   Mapped[str|None]     = mapped_column(String(30))
    is_violation:   Mapped[bool]         = mapped_column(Boolean, default=False)
    violation_type: Mapped[str|None]     = mapped_column(String(50))

    report:   Mapped[ExpenseReport]   = relationship("ExpenseReport", back_populates="lines")
    category: Mapped[ExpenseCategory] = relationship("ExpenseCategory")
