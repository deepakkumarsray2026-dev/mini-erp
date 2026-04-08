from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, EmailStr, field_validator


# ── Department ────────────────────────────────────────────────────────────────

class DepartmentBase(BaseModel):
    code: str
    name: str
    description: str | None = None
    parent_id: str | None = None
    cost_center: str | None = None
    is_active: bool = True

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    parent_id: str | None = None
    manager_id: str | None = None
    cost_center: str | None = None
    is_active: bool | None = None

class DepartmentResponse(DepartmentBase):
    id: str
    manager_id: str | None = None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


# ── Job Family ────────────────────────────────────────────────────────────────

class JobFamilyBase(BaseModel):
    code: str
    name: str
    is_active: bool = True

class JobFamilyCreate(JobFamilyBase):
    pass

class JobFamilyUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None

class JobFamilyResponse(JobFamilyBase):
    id: str
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Job ───────────────────────────────────────────────────────────────────────

class JobBase(BaseModel):
    code: str
    title: str
    job_family_id: str
    grade_min: int | None = None
    grade_max: int | None = None
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    is_active: bool = True

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    title: str | None = None
    grade_min: int | None = None
    grade_max: int | None = None
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    is_active: bool | None = None

class JobResponse(JobBase):
    id: str
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Employee ──────────────────────────────────────────────────────────────────

class EmployeeBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None = None
    date_of_birth: date | None = None
    national_id: str | None = None
    hire_date: date
    employment_type: str = "full_time"
    department_id: str
    job_id: str
    manager_id: str | None = None
    location: str | None = None
    cost_center: str | None = None
    base_salary: Decimal
    currency: str = "GBP"

class EmployeeCreate(EmployeeBase):
    employee_id: str | None = None   # auto-generated if omitted

class EmployeeUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    department_id: str | None = None
    job_id: str | None = None
    manager_id: str | None = None
    location: str | None = None
    cost_center: str | None = None
    base_salary: Decimal | None = None
    employment_type: str | None = None
    employment_status: str | None = None
    satisfaction_score: float | None = None
    performance_rating: float | None = None

class EmployeeResponse(EmployeeBase):
    id: str
    employee_id: str
    employment_status: str
    termination_date: date | None = None
    satisfaction_score: float | None = None
    performance_rating: float | None = None
    overtime_monthly_avg: float | None = None
    training_hours_ytd: float | None = None
    attrition_risk_score: float | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

class EmployeeListResponse(BaseModel):
    id: str
    employee_id: str
    first_name: str
    last_name: str
    email: str
    department_id: str
    job_id: str
    employment_status: str
    employment_type: str
    base_salary: Decimal
    currency: str
    is_active: bool
    model_config = {"from_attributes": True}

class EmployeeTerminateRequest(BaseModel):
    termination_date: date
    reason: str | None = None
