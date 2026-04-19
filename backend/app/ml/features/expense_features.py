"""
expense_features.py
Feature engineering for the Expense Violation Detector.
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from datetime import date
from sqlalchemy import text
from app.core.database import SyncSessionLocal


FEATURE_COLS = [
    "amount",
    "amount_vs_limit_ratio",    # amount / category daily_limit
    "is_weekend",
    "has_receipt",
    "days_since_hire",
    "employee_avg_spend",       # historical avg spend per line for this employee
    "employee_violation_rate",  # historical violation rate for this employee
    "category_encoded",
    "is_billable",
]

TARGET_COL = "is_violation"


def load_training_dataframe() -> pd.DataFrame:
    query = text("""
        WITH emp_stats AS (
            SELECT
                er2.employee_id,
                AVG(el2.amount)                                                AS employee_avg_spend,
                SUM(CASE WHEN el2.is_violation THEN 1 ELSE 0 END)::float
                    / NULLIF(COUNT(el2.id), 0)                                 AS employee_violation_rate
            FROM expenses.expense_lines el2
            JOIN expenses.expense_reports er2 ON er2.id = el2.report_id
            GROUP BY er2.employee_id
        )
        SELECT
            el.id,
            el.amount,
            el.expense_date,
            el.receipt_path,
            el.is_billable,
            el.is_violation,
            el.category_id,
            ec.daily_limit,
            ec.code          AS category_code,
            er.employee_id,
            e.hire_date,
            COALESCE(es.employee_avg_spend, el.amount)      AS employee_avg_spend,
            COALESCE(es.employee_violation_rate, 0)         AS employee_violation_rate
        FROM expenses.expense_lines el
        JOIN expenses.expense_reports er    ON er.id = el.report_id
        JOIN expenses.expense_categories ec ON ec.id = el.category_id
        JOIN hcm.employees e                ON e.id = er.employee_id
        LEFT JOIN emp_stats es              ON es.employee_id = er.employee_id
    """)

    with SyncSessionLocal() as session:
        rows = session.execute(query).fetchall()
        cols = [
            "id", "amount", "expense_date", "receipt_path", "is_billable",
            "is_violation", "category_id", "daily_limit", "category_code",
            "employee_id", "hire_date", "employee_avg_spend", "employee_violation_rate",
        ]
        df = pd.DataFrame(rows, columns=cols)

    df["amount"]            = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    df["daily_limit"]       = pd.to_numeric(df["daily_limit"], errors="coerce").fillna(500)
    df["employee_avg_spend"]= pd.to_numeric(df["employee_avg_spend"], errors="coerce").fillna(df["amount"].median())
    df["employee_violation_rate"] = pd.to_numeric(df["employee_violation_rate"], errors="coerce").fillna(0)

    df["amount_vs_limit_ratio"] = df["amount"] / df["daily_limit"].replace(0, np.nan).fillna(500)
    df["is_weekend"]            = df["expense_date"].apply(lambda d: int(d.weekday() >= 5) if d else 0)
    df["has_receipt"]           = df["receipt_path"].notna().astype(int)
    df["is_billable"]           = df["is_billable"].astype(int)
    df["days_since_hire"]       = df["hire_date"].apply(
        lambda d: (date.today() - d).days if d else 365
    )

    # encode category
    categories = df["category_code"].unique().tolist()
    cat_map    = {c: i for i, c in enumerate(sorted(categories))}
    df["category_encoded"] = df["category_code"].map(cat_map).fillna(0).astype(int)

    return df[FEATURE_COLS + [TARGET_COL, "id"]]


def build_inference_vector(line_dict: dict, employee_dict: dict, category_dict: dict) -> pd.DataFrame:
    amount    = float(line_dict.get("amount", 0))
    limit     = float(category_dict.get("daily_limit") or 500)
    exp_date  = line_dict.get("expense_date")
    hire_date = employee_dict.get("hire_date")

    row = {
        "amount":                 amount,
        "amount_vs_limit_ratio":  amount / max(limit, 1),
        "is_weekend":             int(exp_date.weekday() >= 5) if exp_date else 0,
        "has_receipt":            int(bool(line_dict.get("receipt_path"))),
        "days_since_hire":        (date.today() - hire_date).days if hire_date else 365,
        "employee_avg_spend":     float(employee_dict.get("avg_spend", amount)),
        "employee_violation_rate":float(employee_dict.get("violation_rate", 0.0)),
        "category_encoded":       int(category_dict.get("encoded", 0)),
        "is_billable":            int(line_dict.get("is_billable", False)),
    }
    return pd.DataFrame([row])
