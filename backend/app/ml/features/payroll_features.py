"""
payroll_features.py
Feature engineering for the Payroll Anomaly Detector.
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from sqlalchemy import text
from app.core.database import SyncSessionLocal


FEATURE_COLS = [
    "gross_pay",
    "net_pay",
    "income_tax",
    "employee_ni",
    "employee_pension",
    "gross_vs_monthly_salary",   # gross / (base_salary / 12)
    "net_vs_gross_ratio",
    "tax_rate",                  # income_tax / gross
    "ni_rate",
    "pension_rate",
    "deductions_total",
    "prev_gross_delta",          # % change from previous payslip
    "employment_type_encoded",
]

TARGET_COL = "is_anomalous"


def load_training_dataframe() -> pd.DataFrame:
    query = text("""
        SELECT
            ps.id,
            ps.gross_pay,
            ps.net_pay,
            ps.income_tax,
            ps.employee_ni,
            ps.employee_pension,
            ps.total_deductions,
            ps.is_anomalous,
            e.base_salary,
            e.employment_type,
            LAG(ps.gross_pay) OVER (PARTITION BY ps.employee_id ORDER BY pp.start_date)
                AS prev_gross
        FROM payroll.payslips ps
        JOIN payroll.payroll_runs pr ON pr.id = ps.payroll_run_id
        JOIN payroll.pay_periods   pp ON pp.id = pr.pay_period_id
        JOIN hcm.employees e           ON e.id = ps.employee_id
    """)

    with SyncSessionLocal() as session:
        rows = session.execute(query).fetchall()
        cols = [
            "id", "gross_pay", "net_pay", "income_tax", "employee_ni",
            "employee_pension", "total_deductions", "is_anomalous",
            "base_salary", "employment_type", "prev_gross",
        ]
        df = pd.DataFrame(rows, columns=cols)

    for col in ["gross_pay", "net_pay", "income_tax", "employee_ni",
                "employee_pension", "total_deductions", "base_salary"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    monthly_salary = df["base_salary"] / 12.0
    df["gross_vs_monthly_salary"] = df["gross_pay"] / monthly_salary.replace(0, np.nan).fillna(1)
    df["net_vs_gross_ratio"]      = df["net_pay"]    / df["gross_pay"].replace(0, np.nan).fillna(1)
    df["tax_rate"]                = df["income_tax"] / df["gross_pay"].replace(0, np.nan).fillna(1)
    df["ni_rate"]                 = df["employee_ni"]/ df["gross_pay"].replace(0, np.nan).fillna(1)
    df["pension_rate"]            = df["employee_pension"] / df["gross_pay"].replace(0, np.nan).fillna(1)
    df["deductions_total"]        = df["total_deductions"]

    prev_gross = pd.to_numeric(df["prev_gross"], errors="coerce")
    df["prev_gross_delta"] = (
        (df["gross_pay"] - prev_gross) / prev_gross.replace(0, np.nan)
    ).fillna(0.0)

    type_map = {"full_time": 0, "part_time": 1, "contract": 2, "intern": 3,
                "FULL_TIME": 0, "PART_TIME": 1, "CONTRACT": 2, "INTERN": 3}
    df["employment_type_encoded"] = df["employment_type"].map(type_map).fillna(0).astype(int)

    return df[FEATURE_COLS + [TARGET_COL, "id"]]


def build_inference_vector(payslip_dict: dict, employee_dict: dict, prev_gross: float | None = None) -> pd.DataFrame:
    gross   = float(payslip_dict.get("gross_pay", 0))
    net     = float(payslip_dict.get("net_pay", 0))
    tax     = float(payslip_dict.get("income_tax", 0))
    ni      = float(payslip_dict.get("employee_ni", 0))
    pension = float(payslip_dict.get("employee_pension", 0))
    deduct  = float(payslip_dict.get("total_deductions", 0))
    salary  = float(employee_dict.get("base_salary", gross * 12))
    monthly = salary / 12.0 or 1.0

    type_map = {"full_time": 0, "part_time": 1, "contract": 2, "intern": 3,
                "FULL_TIME": 0, "PART_TIME": 1, "CONTRACT": 2, "INTERN": 3}

    row = {
        "gross_pay":               gross,
        "net_pay":                 net,
        "income_tax":              tax,
        "employee_ni":             ni,
        "employee_pension":        pension,
        "gross_vs_monthly_salary": gross / monthly,
        "net_vs_gross_ratio":      net   / max(gross, 1),
        "tax_rate":                tax   / max(gross, 1),
        "ni_rate":                 ni    / max(gross, 1),
        "pension_rate":            pension / max(gross, 1),
        "deductions_total":        deduct,
        "prev_gross_delta":        (gross - prev_gross) / max(prev_gross, 1) if prev_gross else 0.0,
        "employment_type_encoded": type_map.get(employee_dict.get("employment_type", "full_time"), 0),
    }
    return pd.DataFrame([row])
