import enum
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class PayFrequency(str, enum.Enum):
    WEEKLY      = "weekly"
    BIWEEKLY    = "biweekly"
    SEMIMONTHLY = "semimonthly"
    MONTHLY     = "monthly"


class PayPeriodStatus(str, enum.Enum):
    OPEN       = "open"
    PROCESSING = "processing"
    CALCULATED = "calculated"
    CONFIRMED  = "confirmed"
    CLOSED     = "closed"


class PayComponentType(str, enum.Enum):
    EARNING               = "earning"
    DEDUCTION             = "deduction"
    TAX                   = "tax"
    EMPLOYER_CONTRIBUTION = "employer_contribution"


class PayGroup(Base, TimestampMixin):
    __tablename__ = "pay_groups"
    __table_args__ = {"schema": "payroll"}

    id:        Mapped[str]          = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    code:      Mapped[str]          = mapped_column(String(20), unique=True, nullable=False)
    name:      Mapped[str]          = mapped_column(String(100), nullable=False)
    frequency: Mapped[PayFrequency] = mapped_column(Enum(PayFrequency), nullable=False)
    currency:  Mapped[str]          = mapped_column(String(3), default="GBP")
    is_active: Mapped[bool]         = mapped_column(Boolean, default=True)

    pay_periods: Mapped[list["PayPeriod"]] = relationship("PayPeriod", back_populates="pay_group")


class PayPeriod(Base, TimestampMixin):
    __tablename__ = "pay_periods"
    __table_args__ = (
        UniqueConstraint("pay_group_id", "period_number", "fiscal_year", name="uq_pay_period"),
        {"schema": "payroll"},
    )

    id:            Mapped[str]             = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    pay_group_id:  Mapped[str]             = mapped_column(UUID(as_uuid=False), ForeignKey("payroll.pay_groups.id"))
    period_number: Mapped[int]             = mapped_column(Integer, nullable=False)
    fiscal_year:   Mapped[int]             = mapped_column(Integer, nullable=False)
    start_date:    Mapped[date]            = mapped_column(Date, nullable=False)
    end_date:      Mapped[date]            = mapped_column(Date, nullable=False)
    pay_date:      Mapped[date]            = mapped_column(Date, nullable=False)
    status:        Mapped[PayPeriodStatus] = mapped_column(Enum(PayPeriodStatus), default=PayPeriodStatus.OPEN)

    pay_group:    Mapped[PayGroup]           = relationship("PayGroup", back_populates="pay_periods")
    payroll_runs: Mapped[list["PayrollRun"]] = relationship("PayrollRun", back_populates="pay_period")


class PayComponent(Base, TimestampMixin):
    __tablename__ = "pay_components"
    __table_args__ = {"schema": "payroll"}

    id:               Mapped[str]              = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    code:             Mapped[str]              = mapped_column(String(20), unique=True, nullable=False)
    name:             Mapped[str]              = mapped_column(String(100), nullable=False)
    component_type:   Mapped[PayComponentType] = mapped_column(Enum(PayComponentType), nullable=False)
    is_taxable:       Mapped[bool]             = mapped_column(Boolean, default=True)
    is_pensionable:   Mapped[bool]             = mapped_column(Boolean, default=True)
    gl_account_code:  Mapped[str|None]         = mapped_column(String(20))
    is_active:        Mapped[bool]             = mapped_column(Boolean, default=True)


class PayrollRun(Base, TimestampMixin):
    __tablename__ = "payroll_runs"
    __table_args__ = {"schema": "payroll"}

    id:                     Mapped[str]          = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    pay_period_id:          Mapped[str]          = mapped_column(UUID(as_uuid=False), ForeignKey("payroll.pay_periods.id"))
    run_number:             Mapped[int]          = mapped_column(Integer, default=1)
    status:                 Mapped[str]          = mapped_column(String(20), default="draft")
    total_gross:            Mapped[Decimal]      = mapped_column(Numeric(15, 2), default=0)
    total_deductions:       Mapped[Decimal]      = mapped_column(Numeric(15, 2), default=0)
    total_net:              Mapped[Decimal]      = mapped_column(Numeric(15, 2), default=0)
    total_employer_ni:      Mapped[Decimal]      = mapped_column(Numeric(15, 2), default=0)
    total_employer_pension: Mapped[Decimal]      = mapped_column(Numeric(15, 2), default=0)
    run_by:                 Mapped[str|None]     = mapped_column(UUID(as_uuid=False))
    run_at:                 Mapped[datetime|None]= mapped_column(DateTime(timezone=True))
    anomaly_flags:          Mapped[dict|None]    = mapped_column(JSONB)

    pay_period: Mapped[PayPeriod]        = relationship("PayPeriod", back_populates="payroll_runs")
    payslips:   Mapped[list["PaySlip"]]  = relationship("PaySlip", back_populates="payroll_run")


class PaySlip(Base, TimestampMixin):
    __tablename__ = "payslips"
    __table_args__ = {"schema": "payroll"}

    id:               Mapped[str]      = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    payroll_run_id:   Mapped[str]      = mapped_column(UUID(as_uuid=False), ForeignKey("payroll.payroll_runs.id"))
    employee_id:      Mapped[str]      = mapped_column(UUID(as_uuid=False), ForeignKey("hcm.employees.id"))
    gross_pay:        Mapped[Decimal]  = mapped_column(Numeric(15, 2), nullable=False)
    total_deductions: Mapped[Decimal]  = mapped_column(Numeric(15, 2), nullable=False)
    net_pay:          Mapped[Decimal]  = mapped_column(Numeric(15, 2), nullable=False)
    income_tax:       Mapped[Decimal]  = mapped_column(Numeric(15, 2), default=0)
    employee_ni:      Mapped[Decimal]  = mapped_column(Numeric(15, 2), default=0)
    employee_pension: Mapped[Decimal]  = mapped_column(Numeric(15, 2), default=0)
    employer_ni:      Mapped[Decimal]  = mapped_column(Numeric(15, 2), default=0)
    employer_pension: Mapped[Decimal]  = mapped_column(Numeric(15, 2), default=0)
    line_items:       Mapped[dict]     = mapped_column(JSONB, default=dict)
    is_anomalous:     Mapped[bool]     = mapped_column(Boolean, default=False)
    anomaly_reason:   Mapped[str|None] = mapped_column(Text)

    payroll_run: Mapped[PayrollRun] = relationship("PayrollRun", back_populates="payslips")
    employee:    Mapped["Employee"] = relationship("Employee", back_populates="payslips")
