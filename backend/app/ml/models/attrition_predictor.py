"""
attrition_predictor.py
Random Forest classifier to predict employee attrition risk.
"""
from __future__ import annotations
import os
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, classification_report,
)
from sklearn.pipeline import Pipeline
from imblearn.over_sampling import SMOTE
from loguru import logger

from app.ml.features.employee_features import (
    FEATURE_COLS, TARGET_COL,
    load_training_dataframe, build_inference_vector,
)
from app.core.config import settings
from app.core.database import SyncSessionLocal


MODEL_NAME    = "attrition_predictor"
ARTIFACT_DIR  = Path(settings.MODELS_DIR) / MODEL_NAME
ARTIFACT_PATH = ARTIFACT_DIR / "model.joblib"


def train() -> dict:
    """Train the model, persist to disk, return metrics dict."""
    logger.info(f"[{MODEL_NAME}] Loading training data …")
    df = load_training_dataframe()

    if df.empty or df[TARGET_COL].sum() < 5:
        raise ValueError("Insufficient labelled data for attrition training")

    X = df[FEATURE_COLS].astype(float)
    y = df[TARGET_COL].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # SMOTE to handle class imbalance
    try:
        sm = SMOTE(random_state=42, k_neighbors=min(5, y_train.sum() - 1))
        X_res, y_res = sm.fit_resample(X_train, y_train)
    except Exception:
        X_res, y_res = X_train, y_train

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(
            n_estimators=200,
            max_depth=8,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )),
    ])

    pipeline.fit(X_res, y_res)

    y_pred  = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy":  round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
        "recall":    round(recall_score(y_test, y_pred, zero_division=0), 4),
        "f1_score":  round(f1_score(y_test, y_pred, zero_division=0), 4),
        "roc_auc":   round(roc_auc_score(y_test, y_proba), 4),
        "train_rows": len(X_res),
        "test_rows":  len(X_test),
        "feature_importance": dict(zip(
            FEATURE_COLS,
            pipeline.named_steps["clf"].feature_importances_.round(4).tolist()
        )),
    }

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, ARTIFACT_PATH)
    logger.info(f"[{MODEL_NAME}] Saved → {ARTIFACT_PATH}  AUC={metrics['roc_auc']}")

    return metrics


def predict_all_active(limit: int = 10) -> list[dict]:
    """Batch-score all active employees; return top ``limit`` by risk descending.

    Deduplicates rows that arise from the dept-headcount window JOIN, filters to
    active-only (is_attrited == 0), and enriches results with employee names from DB.
    """
    if not ARTIFACT_PATH.exists():
        raise FileNotFoundError(f"Model not trained yet: {ARTIFACT_PATH}")

    df = load_training_dataframe()
    df = df.drop_duplicates(subset=["id"])
    active = df[df[TARGET_COL] == 0].copy()

    if active.empty:
        return []

    pipeline = joblib.load(ARTIFACT_PATH)
    X = active[FEATURE_COLS].astype(float)
    probas = pipeline.predict_proba(X)[:, 1]
    active = active.copy()
    active["risk_score"] = probas

    top_n = active.nlargest(limit, "risk_score")
    emp_ids = [str(i) for i in top_n["id"].tolist()]

    from sqlalchemy import text as _text
    with SyncSessionLocal() as session:
        rows = session.execute(_text("""
            SELECT e.id::text, e.first_name, e.last_name, e.employee_id,
                   d.name AS department_name
            FROM hcm.employees e
            LEFT JOIN hcm.departments d ON d.id = e.department_id
            WHERE e.id::text = ANY(:ids)
        """), {"ids": emp_ids}).fetchall()

    info = {r[0]: {"first_name": r[1], "last_name": r[2],
                   "employee_number": r[3], "department": r[4]} for r in rows}

    results = []
    for _, row in top_n.iterrows():
        emp = info.get(str(row["id"]), {})
        score = float(row["risk_score"])
        results.append({
            "employee_id":     str(row["id"]),
            "employee_number": emp.get("employee_number", ""),
            "full_name":       f"{emp.get('first_name','')} {emp.get('last_name','')}".strip(),
            "department":      emp.get("department", ""),
            "risk_score":      round(score, 4),
            "risk_pct":        round(score * 100, 1),
            "prediction":      "high_risk" if score >= 0.5 else "low_risk",
        })
    return results


def predict(employee_dict: dict) -> dict:
    """Return attrition risk score and label for one employee."""
    if not ARTIFACT_PATH.exists():
        raise FileNotFoundError(f"Model not trained yet: {ARTIFACT_PATH}")

    import time
    t0       = time.monotonic()
    pipeline = joblib.load(ARTIFACT_PATH)
    X        = build_inference_vector(employee_dict).astype(float)
    proba    = pipeline.predict_proba(X)[0, 1]
    label    = "high_risk" if proba >= 0.5 else "low_risk"

    clf   = pipeline.named_steps["clf"]
    imp   = clf.feature_importances_
    top_k = sorted(zip(FEATURE_COLS, imp), key=lambda t: -t[1])[:5]

    return {
        "prediction":  label,
        "probability": round(float(proba), 4),
        "risk_score":  round(float(proba), 4),
        "top_features": [{"feature": f, "importance": round(float(v), 4)} for f, v in top_k],
        "latency_ms":  round((time.monotonic() - t0) * 1000, 2),
    }
