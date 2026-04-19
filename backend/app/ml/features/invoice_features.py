"""
invoice_features.py
Feature engineering for the Invoice Category Classifier.
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from sqlalchemy import text
from app.core.database import SyncSessionLocal
from sklearn.feature_extraction.text import TfidfVectorizer

NUMERIC_FEATURE_COLS = [
    "total_amount",
    "tax_amount",
    "tax_rate",
    "line_count",
    "avg_line_amount",
    "vendor_invoice_count",     # how many invoices from this vendor historically
    "payment_terms_days",
    "days_to_due",
]

TARGET_COL  = "category"
TFIDF_MAX   = 50   # number of TF-IDF text features

CATEGORIES = [
    "utilities", "software_saas", "office_supplies", "professional_services",
    "travel", "marketing", "hardware", "maintenance", "consulting", "insurance",
]


def load_training_dataframe() -> tuple[pd.DataFrame, pd.Series]:
    """Returns (X numeric+text, y labels)."""
    query = text("""
        WITH vendor_counts AS (
            SELECT vendor_id, COUNT(*) AS vendor_invoice_count
            FROM ap.invoices
            GROUP BY vendor_id
        ),
        line_stats AS (
            SELECT invoice_id, COUNT(*) AS line_count, AVG(amount) AS avg_line_amount
            FROM ap.invoice_lines
            GROUP BY invoice_id
        )
        SELECT
            i.id,
            i.total_amount,
            i.tax_amount,
            i.description,
            i.category,
            i.invoice_date,
            i.due_date,
            COALESCE(ls.line_count, 0)          AS line_count,
            COALESCE(ls.avg_line_amount, 0)     AS avg_line_amount,
            v.payment_terms_days,
            COALESCE(vc.vendor_invoice_count, 1) AS vendor_invoice_count
        FROM ap.invoices i
        JOIN ap.vendors v              ON v.id = i.vendor_id
        LEFT JOIN line_stats ls        ON ls.invoice_id = i.id
        LEFT JOIN vendor_counts vc     ON vc.vendor_id = i.vendor_id
        WHERE i.category IS NOT NULL
    """)

    with SyncSessionLocal() as session:
        rows = session.execute(query).fetchall()
        cols = [
            "id", "total_amount", "tax_amount", "description", "category",
            "invoice_date", "due_date", "line_count", "avg_line_amount",
            "payment_terms_days", "vendor_invoice_count",
        ]
        df = pd.DataFrame(rows, columns=cols)

    if df.empty:
        return pd.DataFrame(), pd.Series(dtype=str)

    for col in ["total_amount", "tax_amount", "avg_line_amount"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    df["tax_rate"] = df["tax_amount"] / df["total_amount"].replace(0, np.nan).fillna(1)
    df["line_count"] = pd.to_numeric(df["line_count"], errors="coerce").fillna(1).astype(int)
    df["payment_terms_days"] = pd.to_numeric(df["payment_terms_days"], errors="coerce").fillna(30).astype(int)
    df["vendor_invoice_count"] = pd.to_numeric(df["vendor_invoice_count"], errors="coerce").fillna(1).astype(int)
    df["days_to_due"] = df.apply(
        lambda r: (r["due_date"] - r["invoice_date"]).days
        if r["due_date"] and r["invoice_date"] else 30, axis=1
    )
    df["avg_line_amount"] = df["avg_line_amount"].fillna(df["total_amount"])

    y = df[TARGET_COL]
    X = df[NUMERIC_FEATURE_COLS + ["description", "id"]]
    return X, y


def build_tfidf_features(descriptions: pd.Series, vectorizer: TfidfVectorizer | None = None,
                          fit: bool = False) -> tuple[pd.DataFrame, TfidfVectorizer]:
    texts = descriptions.fillna("").astype(str)
    if vectorizer is None:
        vectorizer = TfidfVectorizer(max_features=TFIDF_MAX, stop_words="english", ngram_range=(1, 2))
    if fit:
        matrix = vectorizer.fit_transform(texts)
    else:
        matrix = vectorizer.transform(texts)
    tfidf_df = pd.DataFrame(matrix.toarray(),
                            columns=[f"tfidf_{f}" for f in vectorizer.get_feature_names_out()])
    return tfidf_df, vectorizer


def build_inference_vector(invoice_dict: dict, line_dicts: list[dict],
                            vendor_dict: dict, tfidf_vectorizer=None) -> pd.DataFrame:
    total  = float(invoice_dict.get("total_amount", 0))
    tax    = float(invoice_dict.get("tax_amount", 0))
    inv_dt = invoice_dict.get("invoice_date")
    due_dt = invoice_dict.get("due_date")

    numeric_row = {
        "total_amount":         total,
        "tax_amount":           tax,
        "tax_rate":             tax / max(total, 1),
        "line_count":           len(line_dicts),
        "avg_line_amount":      sum(float(l.get("amount", 0)) for l in line_dicts) / max(len(line_dicts), 1),
        "vendor_invoice_count": int(vendor_dict.get("invoice_count", 1)),
        "payment_terms_days":   int(vendor_dict.get("payment_terms_days", 30)),
        "days_to_due":          (due_dt - inv_dt).days if due_dt and inv_dt else 30,
    }
    num_df = pd.DataFrame([numeric_row])

    if tfidf_vectorizer:
        desc = invoice_dict.get("description", "")
        tfidf_df, _ = build_tfidf_features(pd.Series([desc]), tfidf_vectorizer, fit=False)
        return pd.concat([num_df.reset_index(drop=True), tfidf_df.reset_index(drop=True)], axis=1)

    return num_df
