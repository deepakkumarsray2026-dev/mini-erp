import enum
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class AccountType(str, enum.Enum):
    ASSET     = "asset"
    LIABILITY = "liability"
    EQUITY    = "equity"
    REVENUE   = "revenue"
    EXPENSE   = "expense"


class JournalSource(str, enum.Enum):
    MANUAL      = "manual"
    PAYROLL     = "payroll"
    AP          = "accounts_payable"
    EXPENSES    = "expenses"
    PROCUREMENT = "procurement"
    SYSTEM      = "system"


class ChartOfAccounts(Base, TimestampMixin):
    __tablename__ = "chart_of_accounts"
    __table_args__ = {"schema": "gl"}

    id:                Mapped[str]         = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    account_code:      Mapped[str]         = mapped_column(String(20), unique=True, nullable=False)
    account_name:      Mapped[str]         = mapped_column(String(200), nullable=False)
    account_type:      Mapped[AccountType] = mapped_column(Enum(AccountType), nullable=False)
    parent_code:       Mapped[str|None]    = mapped_column(String(20), ForeignKey("gl.chart_of_accounts.account_code"))
    description:       Mapped[str|None]    = mapped_column(Text)
    is_control_account:Mapped[bool]        = mapped_column(Boolean, default=False)
    currency:          Mapped[str]         = mapped_column(String(3), default="GBP")
    is_active:         Mapped[bool]        = mapped_column(Boolean, default=True)
    normal_balance:    Mapped[str]         = mapped_column(String(6), default="debit")

    journal_lines: Mapped[list["JournalLine"]] = relationship("JournalLine", back_populates="account")


class FiscalPeriod(Base, TimestampMixin):
    __tablename__ = "fiscal_periods"
    __table_args__ = (
        UniqueConstraint("fiscal_year", "period_number", name="uq_fiscal_period"),
        {"schema": "gl"},
    )

    id:            Mapped[str]  = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    fiscal_year:   Mapped[int]  = mapped_column(Integer, nullable=False)
    period_number: Mapped[int]  = mapped_column(Integer, nullable=False)
    name:          Mapped[str]  = mapped_column(String(20), nullable=False)
    start_date:    Mapped[date] = mapped_column(Date, nullable=False)
    end_date:      Mapped[date] = mapped_column(Date, nullable=False)
    status:        Mapped[str]  = mapped_column(String(20), default="open")

    journals: Mapped[list["Journal"]] = relationship("Journal", back_populates="fiscal_period")


class Journal(Base, TimestampMixin):
    __tablename__ = "journals"
    __table_args__ = {"schema": "gl"}

    id:               Mapped[str]            = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    journal_number:   Mapped[str]            = mapped_column(String(30), unique=True, nullable=False)
    fiscal_period_id: Mapped[str]            = mapped_column(UUID(as_uuid=False), ForeignKey("gl.fiscal_periods.id"))
    journal_date:     Mapped[date]           = mapped_column(Date, nullable=False)
    description:      Mapped[str]            = mapped_column(Text, nullable=False)
    source:           Mapped[JournalSource]  = mapped_column(Enum(JournalSource), default=JournalSource.MANUAL)
    reference_id:     Mapped[str|None]       = mapped_column(UUID(as_uuid=False))
    total_debit:      Mapped[Decimal]        = mapped_column(Numeric(15, 2), default=0)
    total_credit:     Mapped[Decimal]        = mapped_column(Numeric(15, 2), default=0)
    is_balanced:      Mapped[bool]           = mapped_column(Boolean, default=False)
    posted_by:        Mapped[str|None]       = mapped_column(UUID(as_uuid=False))
    posted_at:        Mapped[datetime|None]  = mapped_column(DateTime(timezone=True))
    status:           Mapped[str]            = mapped_column(String(20), default="draft")
    currency:         Mapped[str]            = mapped_column(String(3), default="GBP")

    fiscal_period: Mapped[FiscalPeriod]       = relationship("FiscalPeriod", back_populates="journals")
    lines:         Mapped[list["JournalLine"]]= relationship("JournalLine", back_populates="journal", cascade="all, delete-orphan")


class JournalLine(Base, TimestampMixin):
    __tablename__ = "journal_lines"
    __table_args__ = {"schema": "gl"}

    id:            Mapped[str]     = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    journal_id:    Mapped[str]     = mapped_column(UUID(as_uuid=False), ForeignKey("gl.journals.id"), nullable=False)
    account_code:  Mapped[str]     = mapped_column(String(20), ForeignKey("gl.chart_of_accounts.account_code"), nullable=False)
    description:   Mapped[str|None]= mapped_column(Text)
    debit:         Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    credit:        Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    department_id: Mapped[str|None]= mapped_column(UUID(as_uuid=False))
    cost_center:   Mapped[str|None]= mapped_column(String(20))
    project_code:  Mapped[str|None]= mapped_column(String(30))

    journal: Mapped[Journal]          = relationship("Journal", back_populates="lines")
    account: Mapped[ChartOfAccounts]  = relationship("ChartOfAccounts", back_populates="journal_lines")


class Budget(Base, TimestampMixin):
    __tablename__ = "budgets"
    __table_args__ = (
        UniqueConstraint("account_code", "department_id", "fiscal_year", "period_number", name="uq_budget"),
        {"schema": "gl"},
    )

    id:                Mapped[str]          = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    fiscal_year:       Mapped[int]          = mapped_column(Integer, nullable=False)
    period_number:     Mapped[int]          = mapped_column(Integer, nullable=False)
    account_code:      Mapped[str]          = mapped_column(String(20), ForeignKey("gl.chart_of_accounts.account_code"))
    department_id:     Mapped[str|None]     = mapped_column(UUID(as_uuid=False))
    budgeted_amount:   Mapped[Decimal]      = mapped_column(Numeric(15, 2), nullable=False)
    actual_amount:     Mapped[Decimal]      = mapped_column(Numeric(15, 2), default=0)
    forecasted_amount: Mapped[Decimal|None] = mapped_column(Numeric(15, 2))
    variance:          Mapped[Decimal]      = mapped_column(Numeric(15, 2), default=0)
    currency:          Mapped[str]          = mapped_column(String(3), default="GBP")
