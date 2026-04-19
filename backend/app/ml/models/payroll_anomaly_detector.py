"""
payroll_anomaly_detector.py

Hybrid anomaly detector for payroll payslips.

Strategy
--------
Supervised path  (preferred):
    ``RandomForestClassifier`` when ``is_anomalous``-labelled rows with at least
    ``_MIN_ANOMALOUS_SAMPLES`` exist.  Uses SMOTE for class-imbalance correction
    and reports standard classification metrics plus cross-validated AUC.

Unsupervised fallback:
    ``IsolationForest`` when labelled data is insufficient.  Decision scores are
    mapped to anomaly probability via a sigmoid so callers always receive a
    ``[0, 1]`` probability regardless of the model mode.

Key features (see payroll_features.py):
    - gross_vs_monthly_salary : detects phantom salary changes
    - net_vs_gross_ratio      : detects unusual deduction levels
    - prev_gross_delta        : detects large period-over-period swings
    - tax_rate / ni_rate      : detects misconfigured payroll components
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
from sklearn.ensemble import IsolationForest, RandomForestClassifier
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
from app.ml.features.payroll_features import (
    FEATURE_COLS,
    TARGET_COL,
    build_inference_vector,
    load_training_dataframe,
)

# ── Constants ─────────────────────────────────────────────────────────────────

MODEL_NAME = "payroll_anomaly_detector"
ARTIFACT_DIR = Path(settings.MODELS_DIR) / MODEL_NAME
ARTIFACT_PATH = ARTIFACT_DIR / "model.joblib"

_MIN_ANOMALOUS_SAMPLES = 10
_ISOLATION_THRESHOLD = -0.05  # tuned for payroll distribution


# ── Training ──────────────────────────────────────────────────────────────────


def train() -> dict[str, Any]:
    """Train the payroll-anomaly detector and persist the artifact to disk.

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
            "ensure payslips and payroll runs exist in the database."
        )

    anomalous_count = int(df[TARGET_COL].sum())
    logger.info(
        f"[{MODEL_NAME}] {len(df)} rows loaded | "
        f"{anomalous_count} anomalous ({anomalous_count / len(df):.1%})"
    )

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    if anomalous_count >= _MIN_ANOMALOUS_SAMPLES:
        return _train_supervised(df)

    logger.warning(
        f"[{MODEL_NAME}] Only {anomalous_count} labelled anomalies found "
        f"(minimum {_MIN_ANOMALOUS_SAMPLES}). Falling back to IsolationForest."
    )
    return _train_isolation_forest(df)


def _train_supervised(df: pd.DataFrame) -> dict[str, Any]:
    """RandomForest supervised path with SMOTE and cross-validated AUC."""
    X = df[FEATURE_COLS].astype(float)
    y = df[TARGET_COL].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

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
                RandomForestClassifier(
                    n_estimators=300,
                    max_depth=10,
                    min_samples_leaf=5,
                    class_weight="balanced",
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    pipeline.fit(X_res, y_res)

    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_auc_scores = cross_val_score(
        Pipeline([
            ("scaler", StandardScaler()),
            ("clf", RandomForestClassifier(
                n_estimators=300, max_depth=10, min_samples_leaf=5,
                class_weight="balanced", random_state=42, n_jobs=-1,
            )),
        ]),
        X_train, y_train, cv=cv, scoring="roc_auc",
    )

    clf = pipeline.named_steps["clf"]
    feature_importances = dict(
        zip(FEATURE_COLS, clf.feature_importances_.round(4).tolist())
    )

    metrics: dict[str, Any] = {
        "mode": "supervised",
        "algorithm": "RandomForestClassifier",
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_test, y_pred, zero_division=0), 4),
        "f1_score": round(f1_score(y_test, y_pred, zero_division=0), 4),
        "roc_auc": round(roc_auc_score(y_test, y_proba), 4),
        "cv_auc_mean": round(float(cv_auc_scores.mean()), 4),
        "cv_auc_std": round(float(cv_auc_scores.std()), 4),
        "train_rows": len(X_res),
        "test_rows": len(X_test),
        "anomalous_samples": int(y.sum()),
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
        n_estimators=300,
        contamination="auto",
        max_features=1.0,
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
        "feature_cols": FEATURE_COLS,
        "contamination": "auto",
    }

    joblib.dump({"mode": "unsupervised", "scaler": scaler, "model": iso}, ARTIFACT_PATH)
    logger.info(f"[{MODEL_NAME}] Saved IsolationForest fallback → {ARTIFACT_PATH}")
    return metrics


# ── Inference ─────────────────────────────────────────────────────────────────


def predict(
    payslip_dict: dict[str, Any],
    employee_dict: dict[str, Any],
    prev_gross: float | None = None,
) -> dict[str, Any]:
    """Predict whether a payslip is anomalous.

    Args:
        payslip_dict:  Raw ``payslips`` fields (gross_pay, net_pay, income_tax, etc.).
        employee_dict: Raw ``employees`` fields (base_salary, employment_type, etc.).
        prev_gross:    Gross pay from the employee's immediately preceding payslip,
                       used to compute the ``prev_gross_delta`` feature.  Pass
                       ``None`` when no prior payslip exists.

    Returns:
        Dictionary containing ``prediction``, ``probability``, ``is_anomalous``,
        ``top_features`` (supervised mode), ``anomaly_score`` (unsupervised mode),
        and ``latency_ms``.

    Raises:
        FileNotFoundError: When the model artifact has not been trained yet.
    """
    if not ARTIFACT_PATH.exists():
        raise FileNotFoundError(
            f"[{MODEL_NAME}] Model artifact not found at {ARTIFACT_PATH}. "
            "Trigger training first via POST /api/v1/mlops/train/payroll_anomaly."
        )

    t0 = time.monotonic()
    artifact = joblib.load(ARTIFACT_PATH)
    X = build_inference_vector(payslip_dict, employee_dict, prev_gross).astype(float)

    if artifact["mode"] == "supervised":
        pipeline: Pipeline = artifact["pipeline"]
        proba = float(pipeline.predict_proba(X)[0, 1])
        is_anomalous = proba >= 0.5

        clf = pipeline.named_steps["clf"]
        importances = clf.feature_importances_
        top_features = sorted(
            zip(FEATURE_COLS, importances.tolist()),
            key=lambda t: -t[1],
        )[:5]

        result: dict[str, Any] = {
            "prediction": "anomalous" if is_anomalous else "normal",
            "is_anomalous": is_anomalous,
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
        is_anomalous = score < _ISOLATION_THRESHOLD
        proba = _score_to_probability(score)

        result = {
            "prediction": "anomalous" if is_anomalous else "normal",
            "is_anomalous": is_anomalous,
            "probability": round(proba, 4),
            "confidence": round(max(proba, 1 - proba), 4),
            "anomaly_score": round(score, 4),
            "model_mode": "unsupervised_isolation_forest",
        }

    result["latency_ms"] = round((time.monotonic() - t0) * 1000, 2)
    return result


# ── Helpers ───────────────────────────────────────────────────────────────────


def _score_to_probability(score: float) -> float:
    """Map an IsolationForest decision score to a [0, 1] anomaly probability.

    The IsolationForest returns negative scores for anomalies.  We centre a
    sigmoid at ``_ISOLATION_THRESHOLD`` so the decision boundary maps to p ≈ 0.5.
    """
    shifted = -(score - _ISOLATION_THRESHOLD) * 8
    return float(1 / (1 + np.exp(-shifted)))
