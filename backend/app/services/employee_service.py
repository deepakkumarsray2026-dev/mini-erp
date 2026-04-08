"""
employee_service.py  —  Workforce CRUD service
"""
from datetime import date
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.hcm import Department, JobFamily, Job, Employee, EmploymentStatus
from app.schemas.workforce import (
    DepartmentCreate, DepartmentUpdate,
    JobFamilyCreate, JobFamilyUpdate,
    JobCreate, JobUpdate,
    EmployeeCreate, EmployeeUpdate, EmployeeTerminateRequest,
)


# ── Departments ───────────────────────────────────────────────────────────────

async def list_departments(db: AsyncSession, active_only: bool = True) -> list[Department]:
    q = select(Department)
    if active_only:
        q = q.where(Department.is_active == True)
    result = await db.execute(q.order_by(Department.name))
    return result.scalars().all()


async def get_department(db: AsyncSession, dept_id: str) -> Department:
    result = await db.execute(select(Department).where(Department.id == dept_id))
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    return dept


async def create_department(db: AsyncSession, data: DepartmentCreate) -> Department:
    existing = await db.execute(select(Department).where(Department.code == data.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Department code '{data.code}' already exists")
    dept = Department(**data.model_dump())
    db.add(dept)
    await db.flush()
    await db.refresh(dept)
    return dept


async def update_department(db: AsyncSession, dept_id: str, data: DepartmentUpdate) -> Department:
    dept = await get_department(db, dept_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(dept, field, value)
    await db.flush()
    await db.refresh(dept)
    return dept


async def delete_department(db: AsyncSession, dept_id: str) -> None:
    dept = await get_department(db, dept_id)
    count = await db.execute(
        select(func.count(Employee.id)).where(Employee.department_id == dept_id, Employee.is_active == True)
    )
    if count.scalar() > 0:
        raise HTTPException(status_code=409, detail="Cannot delete department with active employees")
    dept.is_active = False


# ── Job Families ──────────────────────────────────────────────────────────────

async def list_job_families(db: AsyncSession) -> list[JobFamily]:
    result = await db.execute(select(JobFamily).order_by(JobFamily.name))
    return result.scalars().all()


async def create_job_family(db: AsyncSession, data: JobFamilyCreate) -> JobFamily:
    existing = await db.execute(select(JobFamily).where(JobFamily.code == data.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Job family code '{data.code}' already exists")
    jf = JobFamily(**data.model_dump())
    db.add(jf)
    await db.flush()
    await db.refresh(jf)
    return jf


# ── Jobs ──────────────────────────────────────────────────────────────────────

async def list_jobs(db: AsyncSession, active_only: bool = True) -> list[Job]:
    q = select(Job)
    if active_only:
        q = q.where(Job.is_active == True)
    result = await db.execute(q.order_by(Job.title))
    return result.scalars().all()


async def get_job(db: AsyncSession, job_id: str) -> Job:
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


async def create_job(db: AsyncSession, data: JobCreate) -> Job:
    existing = await db.execute(select(Job).where(Job.code == data.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Job code '{data.code}' already exists")
    job = Job(**data.model_dump())
    db.add(job)
    await db.flush()
    await db.refresh(job)
    return job


async def update_job(db: AsyncSession, job_id: str, data: JobUpdate) -> Job:
    job = await get_job(db, job_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(job, field, value)
    await db.flush()
    await db.refresh(job)
    return job


# ── Employees ─────────────────────────────────────────────────────────────────

async def list_employees(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    search: str = "",
    department_id: str | None = None,
    active_only: bool = True,
) -> tuple[list[Employee], int]:
    q = select(Employee)
    if active_only:
        q = q.where(Employee.is_active == True)
    if department_id:
        q = q.where(Employee.department_id == department_id)
    if search:
        term = f"%{search}%"
        q = q.where(or_(
            Employee.first_name.ilike(term),
            Employee.last_name.ilike(term),
            Employee.email.ilike(term),
            Employee.employee_id.ilike(term),
        ))
    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar()
    result = await db.execute(q.order_by(Employee.last_name, Employee.first_name)
                               .offset((page - 1) * page_size).limit(page_size))
    return result.scalars().all(), total


async def get_employee(db: AsyncSession, employee_id: str) -> Employee:
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


async def create_employee(db: AsyncSession, data: EmployeeCreate) -> Employee:
    existing_email = await db.execute(select(Employee).where(Employee.email == data.email))
    if existing_email.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    payload = data.model_dump()
    if not payload.get("employee_id"):
        count_res = await db.execute(select(func.count(Employee.id)))
        count = count_res.scalar() or 0
        payload["employee_id"] = f"EMP{count + 1:04d}"

    emp = Employee(**payload)
    db.add(emp)
    await db.flush()
    await db.refresh(emp)
    return emp


async def update_employee(db: AsyncSession, employee_id: str, data: EmployeeUpdate) -> Employee:
    emp = await get_employee(db, employee_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(emp, field, value)
    await db.flush()
    await db.refresh(emp)
    return emp


async def terminate_employee(db: AsyncSession, employee_id: str, data: EmployeeTerminateRequest) -> Employee:
    emp = await get_employee(db, employee_id)
    if emp.employment_status == EmploymentStatus.TERMINATED:
        raise HTTPException(status_code=409, detail="Employee is already terminated")
    emp.employment_status = EmploymentStatus.TERMINATED
    emp.termination_date  = data.termination_date
    emp.is_active         = False
    await db.flush()
    await db.refresh(emp)
    return emp


async def get_employee_by_emp_id(db: AsyncSession, emp_id: str) -> Employee | None:
    result = await db.execute(select(Employee).where(Employee.employee_id == emp_id))
    return result.scalar_one_or_none()
