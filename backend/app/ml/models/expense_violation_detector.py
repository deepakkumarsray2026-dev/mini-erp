"""
expense_violation_detector.py

Gradient Boosting classifier to detect expense policy violations.

The model learns from labelled `expenses.expense_lines` rows (is_violation flag)
using features such as amount-vs-limit ratio, day-of-week, receipt presence, and
employee historical spend/violation patterns.  When the labelled minority class is
too small for reliable supervised learning the model falls back to an Isolation
Forest so inference is always available.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from loguru import logger
from sklearn.ensemble import GradientBoostingClassifier, IsolationForest
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.core.config import settings
from app.ml.features.expense_features import (
    FEATURE_COLS,
    TARGET_COL,
    build_inference_vector,
    load_training_dataframe,
)

# ── Constants ─────────────────────────────────────────────────────────────────

MODEL_NAME = "expense_violation_detector"
ARTIFACT_DIR = Path(settings.MODELS_DIR) / MODEL_NAME
ARTIFACT_PATH = ARTIFACT_DIR / "model.joblib"

# Minimum positive-class samples required for supervised training
_MIN_POSITIVE_SAMPLES = 10

# Anomaly score threshold when using the Isolation Forest fallback
_ISOLATION_THRESHOLD = -0.1


# ── Training ──────────────────────────────────────────────────────────────────


def train() -> dict[str, Any]:
    """Train the expense-violation detector and persist the artifact to disk.

    Supervised path (preferred):
        Uses ``GradientBoostingClassifier`` inside an sklearn ``Pipeline`` with
        ``StandardScaler``.  SMOTE is applied when the positive class is under-
        represented.  5-fold cross-validation AUC is reported alongside hold-out
        metrics.

    Unsupervised fallback:
        When fewer than ``_MIN_POSITIVE_SAMPLES`` labelled violations exist the
        model falls back to ``IsolationForest`` so the endpoint remains usable
        while labelled data accumulates.

    Returns:
        Dictionary of evaluation metrics and training metadata.

    Raises:
        ValueError: When the training dataframe is completely empty.
    """
    logger.info(f"[{MODEL_NAME}] Loading training data …")
    df = load_training_dataframe()

    if df.empty:
        raise ValueError(
            f"[{MODEL_NAME}] Training dataframe is empty — "
            "ensure expense_lines exist in the database."
        )

    positive_count = int(df[TARGET_COL].sum())
    logger.info(
        f"[{MODEL_NAME}] {len(df)} rows loaded | "
        f"{positive_count} violations ({positive_count / len(df):.1%})"
    )

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Supervised path ───────────────────────────────────────────────────────
    if positive_count >= _MIN_POSITIVE_SAMPLES:
        return _train_supervised(df)

    # ── Unsupervised fallback ─────────────────────────────────────────────────
    logger.warning(
        f"[{MODEL_NAME}] Only {positive_count} labelled violations found "
        f"(minimum {_MIN_POSITIVE_SAMPLES}). Falling back to IsolationForest."
    )
    return _train_isolation_forest(df)


def _train_supervised(df: pd.DataFrame) -> dict[str, Any]:
    """Gradient Boosting supervised path."""
    X = df[FEATURE_COLS].astype(float)
    y = df[TARGET_COL].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # SMOTE — use at most k_neighbors = min(5, minority_count - 1)
    minority = int(y_train.sum())
    try:
        sm = SMOTE(random_state=42, k_neighbors=min(5, minority - 1))
        X_res, y_res = sm.fit_resample(X_train, y_train)
        logger.debug(f"[{MODEL_NAME}] SMOTE: {len(X_train)} → {len(X_res)} samples")
    except Exception as exc:
        logger.warning(f"[{MODEL_NAME}] SMOTE skipped: {exc}")
        X_res, y_res = X_train, y_train

    pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "clf",
                GradientBoostingClassifier(
                    n_estimators=200,
                    learning_rate=0.05,
                    max_depth=4,
                    min_samples_leaf=10,
                    subsample=0.8,
                    random_state=42,
                ),
            ),
        ]
    )

    pipeline.fit(X_res, y_res)

    # Hold-out metrics
    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    # Cross-validation AUC (on original training fold, not resampled)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_auc_scores = cross_val_score(
        Pipeline([("scaler", StandardScaler()), ("clf", GradientBoostingClassifier(
            n_estimators=200, learning_rate=0.05, max_depth=4,
            min_samples_leaf=10, subsample=0.8, random_state=42,
        ))]),
        X_train, y_train, cv=cv, scoring="roc_auc",
    )

    # Feature importances from the inner estimator
    clf = pipeline.named_steps["clf"]
    feature_importances = dict(
        zip(FEATURE_COLS, clf.feature_importances_.round(4).tolist())
    )

    metrics: dict[str, Any] = {
        "mode": "supervised",
        "algorithm": "GradientBoostingClassifier",
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_test, y_pred, zero_division=0), 4),
        "f1_score": round(f1_score(y_test, y_pred, zero_division=0), 4),
        "roc_auc": round(roc_auc_score(y_test, y_proba), 4),
        "cv_auc_mean": round(float(cv_auc_scores.mean()), 4),
        "cv_auc_std": round(float(cv_auc_scores.std()), 4),
        "train_rows": len(X_res),
        "test_rows": len(X_test),
        "positive_samples": int(y.sum()),
        "feature_importance": feature_importances,
    }

    joblib.dump({"mode": "supervised", "pipeline": pipeline}, ARTIFACT_PATH)
    logger.info(
        f"[{MODEL_NAME}] Saved supervised model → {ARTIFACT_PATH} | "
        f"AUC={metrics['roc_auc']} | CV-AUC={metrics['cv_auc_mean']}±{metrics['cv_auc_std']}"
    )
    return metrics


def _train_isolation_forest(df: pd.DataFrame) -> dict[str, Any]:
    """Unsupervised IsolationForest fallback."""
    X = df[FEATURE_COLS].astype(float)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    iso = IsolationForest(
        n_estimators=200,
        contamination="auto",
        random_state=42,
        n_jobs=-1,
    )
    iso.fit(X_scaled)

    scores = iso.decision_function(X_scaled)
    metrics: dict[str, Any] = {
        "mode": "unsupervised_isolation_forest",
        "algorithm": "IsolationForest",
        "train_rows": len(X),
        "anomaly_score_mean": round(float(scores.mean()), 4),
        "anomaly_score_std": round(float(scores.std()), 4),
        "contamination": "auto",
    }

    joblib.dump({"mode": "unsupervised", "scaler": scaler, "model": iso}, ARTIFACT_PATH)
    logger.info(f"[{MODEL_NAME}] Saved IsolationForest fallback → {ARTIFACT_PATH}")
    return metrics


# ── Batch insight ─────────────────────────────────────────────────────────────


def predict_all_top(limit: int = 10) -> list[dict[str, Any]]:
    """Batch-score all expense lines; return top ``limit`` by violation probability."""
    if not ARTIFACT_PATH.exists():
        raise FileNotFoundError(f"[{MODEL_NAME}] Model artifact not found. Train first.")

    from app.ml.features.expense_features import load_training_dataframe as _load
    df = _load()
    df = df.drop_duplicates(subset=["id"])
    X = df[FEATURE_COLS].astype(float)

    artifact = joblib.load(ARTIFACT_PATH)
    if artifact["mode"] == "supervised":
        probas = artifact["pipeline"].predict_proba(X)[:, 1]
    else:
        X_scaled = artifact["scaler"].transform(X)
        scores = artifact["model"].decision_function(X_scaled)
        probas = np.array([_score_to_probability(float(s)) for s in scores])

    df = df.copy()
    df["probability"] = probas
    top_n = df.nlargest(limit, "probability")
    line_ids = [str(i) for i in top_n["id"].tolist()]

    from sqlalchemy import text as _text
    from app.core.database import SyncSessionLocal
    with SyncSessionLocal() as session:
        rows = session.execute(_text("""
            SELECT el.id::text, el.amount, el.expense_date,
                   ec.name AS category_name,
                   e.first_name || ' ' || e.last_name AS employee_name
            FROM expenses.expense_lines el
            JOIN expenses.expense_reports er   ON er.id = el.report_id
            JOIN expenses.expense_categories ec ON ec.id = el.category_id
            JOIN hcm.employees e               ON e.id = er.employee_id
            WHERE el.id::text = ANY(:ids)
        """), {"ids": line_ids}).fetchall()

    info = {r[0]: {"amount": r[1], "expense_date": r[2],
                   "category": r[3], "employee_name": r[4]} for r in rows}

    results = []
    for _, row in top_n.iterrows():
        line = info.get(str(row["id"]), {})
        prob = float(row["probability"])
        results.append({
            "expense_line_id": str(row["id"]),
            "employee_name":   line.get("employee_name", ""),
            "category":        line.get("category", ""),
            "amount":          float(line.get("amount", 0)),
            "expense_date":    str(line.get("expense_date", "")),
            "probability":     round(prob, 4),
            "risk_pct":        round(prob * 100, 1),
            "prediction":      "violation" if prob >= 0.5 else "compliant",
        })
    return results


# ── Inference ─────────────────────────────────────────────────────────────────


def predict(
    line_dict: dict[str, Any],
    employee_dict: dict[str, Any],
    category_dict: dict[str, Any],
) -> dict[str, Any]:
    """Predict whether an expense line is a policy violation.

    Args:
        line_dict:     Raw ``expense_lines`` fields (amount, expense_date, etc.).
        employee_dict: Raw ``employees`` fields (hire_date, avg_spend, etc.).
        category_dict: Raw ``expense_categories`` fields (daily_limit, encoded, etc.).

    Returns:
        Dictionary containing ``prediction``, ``probability``, ``is_violation``,
        ``top_features`` (supervised only), and ``latency_ms``.

    Raises:
        FileNotFoundError: When the model artifact has not been trained yet.
    """
    if not ARTIFACT_PATH.exists():
        raise FileNotFoundError(
            f"[{MODEL_NAME}] Model artifact not found at {ARTIFACT_PATH}. "
            "Trigger training first via POST /api/v1/mlops/train/expense_violation."
        )

    t0 = time.monotonic()
    artifact = joblib.load(ARTIFACT_PATH)
    X = build_inference_vector(line_dict, employee_dict, category_dict).astype(float)

    if artifact["mode"] == "supervised":
        pipeline: Pipeline = artifact["pipeline"]
        proba = float(pipeline.predict_proba(X)[0, 1])
        label = "violation" if proba >= 0.5 else "compliant"

        clf = pipeline.named_steps["clf"]
        importances = clf.feature_importances_
        top_features = sorted(
            zip(FEATURE_COLS, importances.tolist()),
            key=lambda t: -t[1],
        )[:5]

        result: dict[str, Any] = {
            "prediction": label,
            "is_violation": proba >= 0.5,
            "probability": round(proba, 4),
            "confidence": round(max(proba, 1 - proba), 4),
            "top_features": [
                {"feature": f, "importance": round(v, 4)} for f, v in top_features
            ],
            "model_mode": "supervised",
        }
    else:
        scaler = artifact["scaler"]
        iso: IsolationForest = artifact["model"]
        X_scaled = scaler.transform(X)
        score = float(iso.decision_function(X_scaled)[0])
        is_violation = score < _ISOLATION_THRESHOLD
        proba = _score_to_probability(score)

        result = {
            "prediction": "violation" if is_violation else "compliant",
            "is_violation": is_violation,
            "probability": round(proba, 4),
            "confidence": round(max(proba, 1 - proba), 4),
            "anomaly_score": round(score, 4),
            "model_mode": "unsupervised_isolation_forest",
        }

    result["latency_ms"] = round((time.monotonic() - t0) * 1000, 2)
    return result


# ── Helpers ───────────────────────────────────────────────────────────────────


def _score_to_probability(score: float) -> float:
    """Map an IsolationForest decision score to a [0, 1] violation probability.

    Scores below 0 indicate anomalies; more negative means more anomalous.
    We apply a sigmoid centred at ``_ISOLATION_THRESHOLD`` so that the boundary
    maps to p ≈ 0.5.
    """
    shifted = -(score - _ISOLATION_THRESHOLD) * 5
    return float(1 / (1 + np.exp(-shifted)))
