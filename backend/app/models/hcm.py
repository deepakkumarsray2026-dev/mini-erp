import enum
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class EmploymentStatus(str, enum.Enum):
    ACTIVE     = "active"
    ON_LEAVE   = "on_leave"
    TERMINATED = "terminated"
    SUSPENDED  = "suspended"


class EmploymentType(str, enum.Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT  = "contract"
    INTERN    = "intern"


class Department(Base, TimestampMixin):
    __tablename__ = "departments"
    __table_args__ = {"schema": "hcm"}

    id:          Mapped[str]      = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    code:        Mapped[str]      = mapped_column(String(20), unique=True, nullable=False)
    name:        Mapped[str]      = mapped_column(String(100), nullable=False)
    description: Mapped[str|None] = mapped_column(Text)
    parent_id:   Mapped[str|None] = mapped_column(UUID(as_uuid=False), ForeignKey("hcm.departments.id"))
    manager_id:  Mapped[str|None] = mapped_column(UUID(as_uuid=False), ForeignKey("hcm.employees.id"), nullable=True)
    cost_center: Mapped[str|None] = mapped_column(String(20))
    is_active:   Mapped[bool]     = mapped_column(Boolean, default=True, nullable=False)

    parent:    Mapped["Department|None"]  = relationship("Department", remote_side="Department.id")
    employees: Mapped[list["Employee"]]   = relationship("Employee", foreign_keys="Employee.department_id", back_populates="department")


class JobFamily(Base, TimestampMixin):
    __tablename__ = "job_families"
    __table_args__ = {"schema": "hcm"}

    id:        Mapped[str]  = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    code:      Mapped[str]  = mapped_column(String(20), unique=True, nullable=False)
    name:      Mapped[str]  = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    jobs: Mapped[list["Job"]] = relationship("Job", back_populates="job_family")


class Job(Base, TimestampMixin):
    __tablename__ = "jobs"
    __table_args__ = {"schema": "hcm"}

    id:            Mapped[str]         = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    code:          Mapped[str]         = mapped_column(String(20), unique=True, nullable=False)
    title:         Mapped[str]         = mapped_column(String(100), nullable=False)
    job_family_id: Mapped[str]         = mapped_column(UUID(as_uuid=False), ForeignKey("hcm.job_families.id"))
    grade_min:     Mapped[int|None]    = mapped_column(Integer)
    grade_max:     Mapped[int|None]    = mapped_column(Integer)
    salary_min:    Mapped[Decimal|None]= mapped_column(Numeric(15, 2))
    salary_max:    Mapped[Decimal|None]= mapped_column(Numeric(15, 2))
    is_active:     Mapped[bool]        = mapped_column(Boolean, default=True)

    job_family: Mapped[JobFamily]       = relationship("JobFamily", back_populates="jobs")
    employees:  Mapped[list["Employee"]]= relationship("Employee", back_populates="job")


class Employee(Base, TimestampMixin):
    __tablename__ = "employees"
    __table_args__ = {"schema": "hcm"}

    id:                   Mapped[str]            = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    employee_id:          Mapped[str]            = mapped_column(String(20), unique=True, nullable=False)
    first_name:           Mapped[str]            = mapped_column(String(60), nullable=False)
    last_name:            Mapped[str]            = mapped_column(String(60), nullable=False)
    email:                Mapped[str]            = mapped_column(String(150), unique=True, nullable=False)
    phone:                Mapped[str|None]       = mapped_column(String(30))
    date_of_birth:        Mapped[date|None]      = mapped_column(Date)
    national_id:          Mapped[str|None]       = mapped_column(String(50))
    hire_date:            Mapped[date]           = mapped_column(Date, nullable=False)
    termination_date:     Mapped[date|None]      = mapped_column(Date)
    employment_status:    Mapped[EmploymentStatus]= mapped_column(Enum(EmploymentStatus), default=EmploymentStatus.ACTIVE, nullable=False)
    employment_type:      Mapped[EmploymentType] = mapped_column(Enum(EmploymentType), default=EmploymentType.FULL_TIME, nullable=False)
    department_id:        Mapped[str]            = mapped_column(UUID(as_uuid=False), ForeignKey("hcm.departments.id"), nullable=False)
    job_id:               Mapped[str]            = mapped_column(UUID(as_uuid=False), ForeignKey("hcm.jobs.id"), nullable=False)
    manager_id:           Mapped[str|None]       = mapped_column(UUID(as_uuid=False), ForeignKey("hcm.employees.id"))
    location:             Mapped[str|None]       = mapped_column(String(100))
    cost_center:          Mapped[str|None]       = mapped_column(String(20))
    base_salary:          Mapped[Decimal]        = mapped_column(Numeric(15, 2), nullable=False)
    currency:             Mapped[str]            = mapped_column(String(3), default="GBP", nullable=False)
    satisfaction_score:   Mapped[float|None]     = mapped_column(Numeric(3, 2))
    performance_rating:   Mapped[float|None]     = mapped_column(Numeric(3, 2))
    overtime_monthly_avg: Mapped[float|None]     = mapped_column(Numeric(6, 2))
    training_hours_ytd:   Mapped[float|None]     = mapped_column(Numeric(6, 2))
    attrition_risk_score: Mapped[float|None]     = mapped_column(Numeric(5, 4))
    is_active:            Mapped[bool]           = mapped_column(Boolean, default=True)

    department:      Mapped[Department]              = relationship("Department", foreign_keys=[department_id], back_populates="employees")
    job:             Mapped[Job]                     = relationship("Job", back_populates="employees")
    manager:         Mapped["Employee|None"]         = relationship("Employee", remote_side="Employee.id", foreign_keys=[manager_id])
    payslips:        Mapped[list["PaySlip"]]         = relationship("PaySlip", back_populates="employee")
    expense_reports: Mapped[list["ExpenseReport"]]   = relationship("ExpenseReport", back_populates="employee")
