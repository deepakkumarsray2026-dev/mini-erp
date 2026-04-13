"""
Workforce API  —  Departments, Job Families, Jobs, Employees
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import (
    require_permission, ModuleName, Action,
    can_read, can_create, can_update, can_delete,
)
from app.schemas.workforce import (
    DepartmentCreate, DepartmentUpdate, DepartmentResponse,
    JobFamilyCreate, JobFamilyResponse,
    JobCreate, JobUpdate, JobResponse,
    EmployeeCreate, EmployeeUpdate, EmployeeResponse,
    EmployeeListResponse, EmployeeTerminateRequest,
)
from app.schemas.common import PaginatedResponse, MessageResponse, paginate
from app.services import employee_service

router = APIRouter()


# ── Departments ───────────────────────────────────────────────────────────────

@router.get("/departments", response_model=PaginatedResponse[DepartmentResponse])
async def list_departments(
    active_only: bool = True,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _=Depends(can_read(ModuleName.WORKFORCE)),
    db: AsyncSession = Depends(get_db),
):
    items, total = await employee_service.list_departments(db, active_only, page, page_size)
    return paginate(items, total, page, page_size)


@router.post("/departments", response_model=DepartmentResponse, status_code=201)
async def create_department(
    data: DepartmentCreate,
    _=Depends(can_create(ModuleName.WORKFORCE)),
    db: AsyncSession = Depends(get_db),
):
    return await employee_service.create_department(db, data)


@router.get("/departments/{dept_id}", response_model=DepartmentResponse)
async def get_department(
    dept_id: str,
    _=Depends(can_read(ModuleName.WORKFORCE)),
    db: AsyncSession = Depends(get_db),
):
    return await employee_service.get_department(db, dept_id)


@router.patch("/departments/{dept_id}", response_model=DepartmentResponse)
async def update_department(
    dept_id: str,
    data: DepartmentUpdate,
    _=Depends(can_update(ModuleName.WORKFORCE)),
    db: AsyncSession = Depends(get_db),
):
    return await employee_service.update_department(db, dept_id, data)


@router.delete("/departments/{dept_id}", response_model=MessageResponse)
async def delete_department(
    dept_id: str,
    _=Depends(can_delete(ModuleName.WORKFORCE)),
    db: AsyncSession = Depends(get_db),
):
    await employee_service.delete_department(db, dept_id)
    return {"message": "Department deactivated"}


# ── Job Families ──────────────────────────────────────────────────────────────

@router.get("/job-families", response_model=list[JobFamilyResponse])
async def list_job_families(
    _=Depends(can_read(ModuleName.WORKFORCE)),
    db: AsyncSession = Depends(get_db),
):
    return await employee_service.list_job_families(db)


@router.post("/job-families", response_model=JobFamilyResponse, status_code=201)
async def create_job_family(
    data: JobFamilyCreate,
    _=Depends(can_create(ModuleName.WORKFORCE)),
    db: AsyncSession = Depends(get_db),
):
    return await employee_service.create_job_family(db, data)


# ── Jobs ──────────────────────────────────────────────────────────────────────

@router.get("/jobs", response_model=list[JobResponse])
async def list_jobs(
    active_only: bool = True,
    _=Depends(can_read(ModuleName.WORKFORCE)),
    db: AsyncSession = Depends(get_db),
):
    return await employee_service.list_jobs(db, active_only)


@router.post("/jobs", response_model=JobResponse, status_code=201)
async def create_job(
    data: JobCreate,
    _=Depends(can_create(ModuleName.WORKFORCE)),
    db: AsyncSession = Depends(get_db),
):
    return await employee_service.create_job(db, data)


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    _=Depends(can_read(ModuleName.WORKFORCE)),
    db: AsyncSession = Depends(get_db),
):
    return await employee_service.get_job(db, job_id)


@router.patch("/jobs/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: str,
    data: JobUpdate,
    _=Depends(can_update(ModuleName.WORKFORCE)),
    db: AsyncSession = Depends(get_db),
):
    return await employee_service.update_job(db, job_id, data)


# ── Employees ─────────────────────────────────────────────────────────────────

@router.get("/employees", response_model=PaginatedResponse[EmployeeListResponse])
async def list_employees(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = "",
    department_id: str | None = None,
    active_only: bool = True,
    _=Depends(can_read(ModuleName.WORKFORCE)),
    db: AsyncSession = Depends(get_db),
):
    employees, total = await employee_service.list_employees(
        db, page, page_size, search, department_id, active_only
    )
    items = [
        {
            "id":                e.id,
            "employee_number":   e.employee_id,
            "employee_id":       e.employee_id,
            "full_name":         f"{e.first_name} {e.last_name}",
            "first_name":        e.first_name,
            "last_name":         e.last_name,
            "email":             e.email,
            "department_name":   e.department.name if e.department else None,
            "department_id":     e.department_id,
            "job_title":         e.job.title if e.job else None,
            "job_id":            e.job_id,
            "hire_date":         e.hire_date,
            "employment_status": e.employment_status,
            "employment_type":   e.employment_type,
            "base_salary":       e.base_salary,
            "currency":          e.currency,
            "is_active":         e.is_active,
        }
        for e in employees
    ]
    return paginate(items, total, page, page_size)


@router.post("/employees", response_model=EmployeeResponse, status_code=201)
async def create_employee(
    data: EmployeeCreate,
    _=Depends(can_create(ModuleName.WORKFORCE)),
    db: AsyncSession = Depends(get_db),
):
    return await employee_service.create_employee(db, data)


@router.get("/employees/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: str,
    _=Depends(can_read(ModuleName.WORKFORCE)),
    db: AsyncSession = Depends(get_db),
):
    return await employee_service.get_employee(db, employee_id)


@router.patch("/employees/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: str,
    data: EmployeeUpdate,
    _=Depends(can_update(ModuleName.WORKFORCE)),
    db: AsyncSession = Depends(get_db),
):
    return await employee_service.update_employee(db, employee_id, data)


@router.post("/employees/{employee_id}/terminate", response_model=EmployeeResponse)
async def terminate_employee(
    employee_id: str,
    data: EmployeeTerminateRequest,
    _=Depends(can_update(ModuleName.WORKFORCE)),
    db: AsyncSession = Depends(get_db),
):
    return await employee_service.terminate_employee(db, employee_id, data)
