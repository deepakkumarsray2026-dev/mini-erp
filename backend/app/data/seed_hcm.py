"""
Seed HCM — departments, job families, jobs, 200 employees.
Embeds ML-detectable patterns:
  - High attrition risk: low satisfaction + high overtime + low performance
  - Low attrition risk:  high satisfaction + training hours + promotions
"""
import random
from datetime import date, timedelta
from decimal import Decimal
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.hcm import Department, JobFamily, Job, Employee, EmploymentStatus, EmploymentType

fake = Faker("en_GB")
random.seed(42)
Faker.seed(42)

DEPARTMENTS = [
    ("EXEC",  "Executive",          None,    "CC-001"),
    ("FIN",   "Finance",            None,    "CC-002"),
    ("HR",    "Human Resources",    None,    "CC-003"),
    ("IT",    "Information Technology", None,"CC-004"),
    ("OPS",   "Operations",         None,    "CC-005"),
    ("SALES", "Sales",              None,    "CC-006"),
    ("MKT",   "Marketing",          None,    "CC-007"),
    ("PROC",  "Procurement",        None,    "CC-008"),
    ("LEGAL", "Legal",              None,    "CC-009"),
    ("CS",    "Customer Success",   None,    "CC-010"),
    ("FIN-AP","Accounts Payable",   "FIN",   "CC-011"),
    ("FIN-GL","General Ledger",     "FIN",   "CC-012"),
    ("IT-DEV","Software Development","IT",   "CC-013"),
    ("IT-INF","Infrastructure",     "IT",    "CC-014"),
    ("OPS-WH","Warehouse",          "OPS",   "CC-015"),
]

JOB_FAMILIES = [
    ("MGMT",  "Management"),
    ("FIN",   "Finance"),
    ("IT",    "Technology"),
    ("HR",    "People"),
    ("OPS",   "Operations"),
    ("SALES", "Sales"),
    ("LEGAL", "Legal"),
]

JOBS = [
    # (code, title, family, grade_min, grade_max, salary_min, salary_max)
    ("CEO",    "Chief Executive Officer",     "MGMT",  10, 10, 150000, 250000),
    ("CFO",    "Chief Financial Officer",     "MGMT",   9,  9, 120000, 180000),
    ("CTO",    "Chief Technology Officer",    "MGMT",   9,  9, 120000, 180000),
    ("DIR",    "Director",                    "MGMT",   8,  8,  90000, 140000),
    ("MGR",    "Manager",                     "MGMT",   7,  7,  60000,  90000),
    ("FACCT",  "Financial Accountant",        "FIN",    5,  6,  35000,  55000),
    ("MACCO",  "Management Accountant",       "FIN",    5,  6,  38000,  58000),
    ("APCLK",  "AP Clerk",                    "FIN",    3,  4,  25000,  35000),
    ("GLCLK",  "GL Accountant",               "FIN",    4,  5,  30000,  45000),
    ("SWE",    "Software Engineer",           "IT",     5,  7,  45000,  85000),
    ("SRWE",   "Senior Software Engineer",    "IT",     7,  8,  70000, 110000),
    ("DBA",    "Database Administrator",      "IT",     5,  6,  45000,  70000),
    ("DEVOPS", "DevOps Engineer",             "IT",     6,  7,  55000,  85000),
    ("HRBP",   "HR Business Partner",        "HR",     5,  6,  35000,  55000),
    ("HRCO",   "HR Coordinator",             "HR",     3,  4,  25000,  38000),
    ("OPSMG",  "Operations Manager",         "OPS",    7,  7,  55000,  80000),
    ("WRKR",   "Operations Worker",          "OPS",    2,  3,  22000,  32000),
    ("SALES",  "Sales Executive",            "SALES",  4,  6,  30000,  60000),
    ("SMGR",   "Sales Manager",              "SALES",  7,  7,  55000,  80000),
    ("LEGAL",  "Legal Counsel",              "LEGAL",  7,  8,  65000, 100000),
    ("PROC",   "Procurement Specialist",     "OPS",    4,  5,  30000,  50000),
]

LOCATIONS = ["London", "Manchester", "Birmingham", "Leeds", "Edinburgh", "Bristol", "Remote"]


def random_hire_date(years_back: int = 10) -> date:
    days = random.randint(30, years_back * 365)
    return date.today() - timedelta(days=days)


def calc_years(hire_date: date, term_date: date | None = None) -> float:
    end = term_date or date.today()
    return round((end - hire_date).days / 365.25, 2)


def gen_ml_features(years: float, is_high_risk: bool) -> dict:
    """Generate correlated ML features based on attrition risk profile."""
    if is_high_risk:
        return {
            "satisfaction_score":   round(random.uniform(1.0, 2.5), 2),
            "performance_rating":   round(random.uniform(1.5, 3.0), 2),
            "overtime_monthly_avg": round(random.uniform(20, 60), 2),
            "training_hours_ytd":   round(random.uniform(0, 10), 2),
        }
    else:
        return {
            "satisfaction_score":   round(random.uniform(3.5, 5.0), 2),
            "performance_rating":   round(random.uniform(3.5, 5.0), 2),
            "overtime_monthly_avg": round(random.uniform(0, 15), 2),
            "training_hours_ytd":   round(random.uniform(20, 80), 2),
        }


async def run(db: AsyncSession) -> dict:
    print("Seeding HCM...")
    result = await db.execute(select(func.count()).select_from(Department))
    if result.scalar() > 0:
        print("  HCM already seeded — skipping")
        emp_result = await db.execute(select(Employee))
        emps = emp_result.scalars().all()
        dept_result = await db.execute(select(Department))
        depts = {d.code: d for d in dept_result.scalars().all()}
        return {"employees": emps, "departments": depts}

    # ── Departments ───────────────────────────────────────────────────────────
    dept_map = {}
    for code, name, parent_code, cost_center in DEPARTMENTS:
        dept = Department(code=code, name=name, cost_center=cost_center)
        db.add(dept)
        dept_map[code] = dept
    await db.flush()

    # Set parent relationships
    for code, name, parent_code, _ in DEPARTMENTS:
        if parent_code:
            dept_map[code].parent_id = dept_map[parent_code].id
    await db.flush()
    print(f"  Created {len(dept_map)} departments")

    # ── Job families ──────────────────────────────────────────────────────────
    family_map = {}
    for code, name in JOB_FAMILIES:
        jf = JobFamily(code=code, name=name)
        db.add(jf)
        family_map[code] = jf
    await db.flush()

    # ── Jobs ──────────────────────────────────────────────────────────────────
    job_map = {}
    for code, title, family_code, gmin, gmax, smin, smax in JOBS:
        job = Job(
            code=code, title=title,
            job_family_id=family_map[family_code].id,
            grade_min=gmin, grade_max=gmax,
            salary_min=Decimal(str(smin)),
            salary_max=Decimal(str(smax)),
        )
        db.add(job)
        job_map[code] = job
    await db.flush()
    print(f"  Created {len(job_map)} jobs")

    # ── Employees ─────────────────────────────────────────────────────────────
    employees = []
    dept_codes = list(dept_map.keys())
    job_codes  = list(job_map.keys())

    # Assign jobs to departments realistically
    dept_job_map = {
        "EXEC": ["CEO", "CFO", "CTO"],
        "FIN":  ["DIR", "MGR", "FACCT", "MACCO"],
        "FIN-AP": ["APCLK", "MGR"],
        "FIN-GL": ["GLCLK", "MGR"],
        "HR":   ["DIR", "MGR", "HRBP", "HRCO"],
        "IT":   ["DIR", "MGR", "SWE", "SRWE", "DBA", "DEVOPS"],
        "IT-DEV": ["SWE", "SRWE", "MGR"],
        "IT-INF": ["DBA", "DEVOPS", "MGR"],
        "OPS":  ["DIR", "MGR", "OPSMG", "WRKR"],
        "OPS-WH": ["WRKR", "MGR"],
        "SALES": ["DIR", "MGR", "SALES", "SMGR"],
        "MKT":  ["DIR", "MGR"],
        "PROC": ["MGR", "PROC"],
        "LEGAL": ["DIR", "LEGAL"],
        "CS":   ["MGR", "SALES"],
    }

    emp_counter = 1
    managers = []

    for i in range(200):
        emp_id = f"EMP-{emp_counter:05d}"
        emp_counter += 1

        dept_code = random.choice(dept_codes)
        job_code  = random.choice(dept_job_map.get(dept_code, job_codes))
        job       = job_map[job_code]

        hire_date    = random_hire_date(10)
        years        = calc_years(hire_date)
        is_high_risk = random.random() < 0.25   # 25% high attrition risk
        ml_features  = gen_ml_features(years, is_high_risk)

        salary = Decimal(str(round(
            random.uniform(
                float(job.salary_min or 25000),
                float(job.salary_max or 80000)
            ), -2
        )))

        # 15% terminated (for attrition model training)
        is_terminated = random.random() < 0.15
        term_date = None
        if is_terminated:
            term_days_max = max(91, int(years * 365))
            term_date = hire_date + timedelta(days=random.randint(90, term_days_max))
            if term_date > date.today():
                term_date = date.today() - timedelta(days=30)

        emp = Employee(
            employee_id=emp_id,
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=f"{emp_id.lower()}@mini-erp.local",
            phone=fake.phone_number()[:20],
            date_of_birth=fake.date_of_birth(minimum_age=22, maximum_age=60),
            hire_date=hire_date,
            termination_date=term_date,
            employment_status=EmploymentStatus.TERMINATED if is_terminated else EmploymentStatus.ACTIVE,
            employment_type=random.choice([EmploymentType.FULL_TIME] * 8 + [EmploymentType.PART_TIME, EmploymentType.CONTRACT]),
            department_id=dept_map[dept_code].id,
            job_id=job.id,
            location=random.choice(LOCATIONS),
            cost_center=dept_map[dept_code].cost_center,
            base_salary=salary,
            currency="GBP",
            satisfaction_score=Decimal(str(ml_features["satisfaction_score"])),
            performance_rating=Decimal(str(ml_features["performance_rating"])),
            overtime_monthly_avg=Decimal(str(ml_features["overtime_monthly_avg"])),
            training_hours_ytd=Decimal(str(ml_features["training_hours_ytd"])),
            is_active=not is_terminated,
        )
        db.add(emp)
        employees.append(emp)

        if job_code in ["MGR", "DIR", "CEO", "CFO", "CTO", "SRWE", "SMGR", "OPSMG"]:
            managers.append(emp)

    await db.flush()

    # Assign managers
    for emp in employees:
        eligible = [m for m in managers if m.id != emp.id and m.department_id == emp.department_id]
        if eligible:
            emp.manager_id = random.choice(eligible).id
    await db.flush()

    await db.commit()
    print(f"  Created 200 employees ({sum(1 for e in employees if not e.is_active)} terminated)")
    return {"employees": employees, "departments": dept_map}
