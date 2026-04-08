"""
employee_features.py
Feature engineering for the Attrition Predictor model.
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from datetime import date
from sqlalchemy import text
from app.core.database import SyncSessionLocal


FEATURE_COLS = [
    "tenure_years",
    "age_years",
    "satisfaction_score",
    "performance_rating",
    "overtime_monthly_avg",
    "training_hours_ytd",
    "salary_grade_ratio",       # base_salary / job.salary_max
    "is_manager",
    "dept_headcount",
    "employment_type_encoded",  # 0=full_time,1=part_time,2=contract,3=intern
]

TARGET_COL = "is_attrited"


def load_training_dataframe() -> pd.DataFrame:
    """Load and engineer features from the DB for model training."""
    query = text("""
        SELECT
            e.id,
            e.hire_date,
            e.date_of_birth,
            e.satisfaction_score,
            e.performance_rating,
            e.overtime_monthly_avg,
            e.training_hours_ytd,
            e.base_salary,
            e.employment_type,
            e.employment_status,
            e.manager_id,
            j.salary_min,
            j.salary_max,
            COUNT(e2.id) OVER (PARTITION BY e.department_id) AS dept_headcount
        FROM hcm.employees e
        JOIN hcm.jobs j ON j.id = e.job_id
        LEFT JOIN hcm.employees e2 ON e2.department_id = e.department_id
    """)

    with SyncSessionLocal() as session:
        rows = session.execute(query).fetchall()
        columns = [
            "id", "hire_date", "date_of_birth", "satisfaction_score",
            "performance_rating", "overtime_monthly_avg", "training_hours_ytd",
            "base_salary", "employment_type", "employment_status",
            "manager_id", "salary_min", "salary_max", "dept_headcount",
        ]
        df = pd.DataFrame(rows, columns=columns)

    today = date.today()

    # tenure in years
    df["tenure_years"] = df["hire_date"].apply(
        lambda d: (today - d).days / 365.25 if d else 0.0
    )

    # age in years
    df["age_years"] = df["date_of_birth"].apply(
        lambda d: (today - d).days / 365.25 if d else 35.0
    )

    # salary grade ratio
    df["salary_grade_ratio"] = df.apply(
        lambda r: float(r["base_salary"]) / float(r["salary_max"])
        if r["salary_max"] and float(r["salary_max"]) > 0 else 1.0,
        axis=1,
    )

    # is_manager: has at least one direct report
    manager_ids = df[df["manager_id"].notna()]["manager_id"].unique()
    df["is_manager"] = df["id"].isin(manager_ids).astype(int)

    # employment type encoding
    type_map = {"full_time": 0, "part_time": 1, "contract": 2, "intern": 3}
    df["employment_type_encoded"] = df["employment_type"].map(type_map).fillna(0).astype(int)

    # target
    df[TARGET_COL] = (df["employment_status"] == "terminated").astype(int)

    # fill nulls with medians
    for col in ["satisfaction_score", "performance_rating", "overtime_monthly_avg", "training_hours_ytd"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(df[col].median())

    df["dept_headcount"] = pd.to_numeric(df["dept_headcount"], errors="coerce").fillna(10)

    return df[FEATURE_COLS + [TARGET_COL, "id"]]


def build_inference_vector(employee_dict: dict) -> pd.DataFrame:
    """Build a single-row feature DataFrame from a raw employee dict."""
    today = date.today()
    hire_date = employee_dict.get("hire_date")
    dob       = employee_dict.get("date_of_birth")

    tenure = (today - hire_date).days / 365.25 if hire_date else 0.0
    age    = (today - dob).days / 365.25 if dob else 35.0

    salary     = float(employee_dict.get("base_salary", 0))
    salary_max = float(employee_dict.get("salary_max", salary or 1))
    grade_ratio = salary / salary_max if salary_max > 0 else 1.0

    type_map = {"full_time": 0, "part_time": 1, "contract": 2, "intern": 3}
    etype_enc = type_map.get(employee_dict.get("employment_type", "full_time"), 0)

    row = {
        "tenure_years":           tenure,
        "age_years":               age,
        "satisfaction_score":      float(employee_dict.get("satisfaction_score") or 3.0),
        "performance_rating":      float(employee_dict.get("performance_rating") or 3.0),
        "overtime_monthly_avg":    float(employee_dict.get("overtime_monthly_avg") or 0.0),
        "training_hours_ytd":      float(employee_dict.get("training_hours_ytd") or 0.0),
        "salary_grade_ratio":      grade_ratio,
        "is_manager":              int(employee_dict.get("is_manager", 0)),
        "dept_headcount":          int(employee_dict.get("dept_headcount", 10)),
        "employment_type_encoded": etype_enc,
    }
    return pd.DataFrame([row])
