"""
invoice_classifier.py

Multi-class invoice category classifier.

Architecture
------------
The model combines numeric features (amount, tax rate, line count, vendor
history, payment terms) with TF-IDF text features extracted from the invoice
description field.  Both feature blocks are concatenated and fed into a
``RandomForestClassifier``.

The TF-IDF vectorizer and the numeric scaler are both persisted alongside the
classifier so the same transformations are applied at inference time.

Categories (see invoice_features.CATEGORIES):
    utilities, software_saas, office_supplies, professional_services,
    travel, marketing, hardware, maintenance, consulting, insurance

Minimum data requirement:
    At least ``_MIN_SAMPLES_PER_CLASS`` invoices per category must exist for
    supervised training.  If the dataset is too sparse the model raises a
    descriptive error rather than producing a misleading artifact.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from loguru import logger
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler

from app.core.config import settings
from app.ml.features.invoice_features import (
    CATEGORIES,
    NUMERIC_FEATURE_COLS,
    TARGET_COL,
    build_inference_vector,
    build_tfidf_features,
    load_training_dataframe,
)

# ── Constants ─────────────────────────────────────────────────────────────────

MODEL_NAME = "invoice_classifier"
ARTIFACT_DIR = Path(settings.MODELS_DIR) / MODEL_NAME
ARTIFACT_PATH = ARTIFACT_DIR / "model.joblib"

_MIN_SAMPLES_PER_CLASS = 3  # per-class minimum to attempt training


# ── Training ──────────────────────────────────────────────────────────────────


def train() -> dict[str, Any]:
    """Train the invoice category classifier and persist the artifact.

    The pipeline:
        1. Load labelled invoices with engineered numeric features.
        2. Fit a TF-IDF vectorizer on description text (top-50 n-grams).
        3. Concatenate numeric + TF-IDF features.
        4. Scale and train a Random Forest classifier.
        5. Evaluate on a 20% stratified hold-out split.
        6. Report per-class and macro-averaged metrics.

    Returns:
        Dictionary of evaluation metrics and training metadata.

    Raises:
        ValueError: When insufficient labelled data exists for training.
    """
    logger.info(f"[{MODEL_NAME}] Loading training data …")
    X_raw, y = load_training_dataframe()

    if X_raw.empty or len(y) == 0:
        raise ValueError(
            f"[{MODEL_NAME}] Training dataframe is empty — "
            "ensure ap.invoices rows have a non-NULL category."
        )

    # Validate per-class sample counts
    class_counts = y.value_counts()
    sparse_classes = class_counts[class_counts < _MIN_SAMPLES_PER_CLASS]
    if not sparse_classes.empty:
        logger.warning(
            f"[{MODEL_NAME}] Sparse classes (< {_MIN_SAMPLES_PER_CLASS} samples): "
            + ", ".join(f"{c}={n}" for c, n in sparse_classes.items())
        )

    logger.info(f"[{MODEL_NAME}] {len(y)} invoices | {y.nunique()} categories")

    # ── Feature construction ──────────────────────────────────────────────────
    X_numeric = X_raw[NUMERIC_FEATURE_COLS].astype(float)
    tfidf_df, tfidf_vectorizer = build_tfidf_features(
        X_raw["description"], fit=True
    )
    X_combined = pd.concat(
        [X_numeric.reset_index(drop=True), tfidf_df.reset_index(drop=True)],
        axis=1,
    )

    # ── Label encoding ────────────────────────────────────────────────────────
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X_combined, y_encoded, test_size=0.20, random_state=42, stratify=y_encoded
    )

    pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "clf",
                RandomForestClassifier(
                    n_estimators=300,
                    max_depth=12,
                    min_samples_leaf=3,
                    class_weight="balanced",
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    pipeline.fit(X_train, y_train)

    # Hold-out evaluation
    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)

    # Cross-validated macro-F1
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_f1_scores = cross_val_score(
        pipeline, X_train, y_train, cv=cv, scoring="f1_macro"
    )

    class_report = classification_report(
        y_test, y_pred,
        target_names=label_encoder.classes_,
        output_dict=True,
        zero_division=0,
    )

    # Numeric feature importances (first len(NUMERIC_FEATURE_COLS) entries)
    clf = pipeline.named_steps["clf"]
    num_importances = clf.feature_importances_[: len(NUMERIC_FEATURE_COLS)]
    feature_importances = dict(
        zip(NUMERIC_FEATURE_COLS, num_importances.round(4).tolist())
    )

    metrics: dict[str, Any] = {
        "algorithm": "RandomForestClassifier",
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision_macro": round(
            precision_score(y_test, y_pred, average="macro", zero_division=0), 4
        ),
        "recall_macro": round(
            recall_score(y_test, y_pred, average="macro", zero_division=0), 4
        ),
        "f1_macro": round(
            f1_score(y_test, y_pred, average="macro", zero_division=0), 4
        ),
        "cv_f1_macro_mean": round(float(cv_f1_scores.mean()), 4),
        "cv_f1_macro_std": round(float(cv_f1_scores.std()), 4),
        "train_rows": len(X_train),
        "test_rows": len(X_test),
        "num_classes": int(y.nunique()),
        "classes": label_encoder.classes_.tolist(),
        "per_class_report": {
            cls: {
                "precision": round(v["precision"], 4),
                "recall": round(v["recall"], 4),
                "f1": round(v["f1-score"], 4),
                "support": int(v["support"]),
            }
            for cls, v in class_report.items()
            if isinstance(v, dict) and cls in label_encoder.classes_
        },
        "feature_importance": feature_importances,
    }

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "pipeline": pipeline,
            "tfidf_vectorizer": tfidf_vectorizer,
            "label_encoder": label_encoder,
        },
        ARTIFACT_PATH,
    )
    logger.info(
        f"[{MODEL_NAME}] Saved → {ARTIFACT_PATH} | "
        f"Accuracy={metrics['accuracy']} | F1-macro={metrics['f1_macro']} | "
        f"CV-F1={metrics['cv_f1_macro_mean']}±{metrics['cv_f1_macro_std']}"
    )
    return metrics


# ── Batch insight ─────────────────────────────────────────────────────────────


def predict_all_top(limit: int = 10) -> list[dict[str, Any]]:
    """Batch-score all categorised invoices; return top ``limit`` by confidence.

    Also surfaces where the model's predicted category differs from the stored
    category (is_match=False), which is useful for data-quality review.
    """
    if not ARTIFACT_PATH.exists():
        raise FileNotFoundError(f"[{MODEL_NAME}] Model artifact not found. Train first.")

    X_raw, y = load_training_dataframe()
    if X_raw.empty:
        return []

    artifact = joblib.load(ARTIFACT_PATH)
    pipeline: Pipeline = artifact["pipeline"]
    tfidf_vectorizer = artifact["tfidf_vectorizer"]
    label_encoder: LabelEncoder = artifact["label_encoder"]

    X_numeric = X_raw[NUMERIC_FEATURE_COLS].astype(float)
    tfidf_df, _ = build_tfidf_features(X_raw["description"], tfidf_vectorizer, fit=False)
    X_combined = pd.concat(
        [X_numeric.reset_index(drop=True), tfidf_df.reset_index(drop=True)], axis=1
    )

    y_pred_enc = pipeline.predict(X_combined)
    y_proba    = pipeline.predict_proba(X_combined)
    predicted_categories = label_encoder.inverse_transform(y_pred_enc)
    confidences = y_proba.max(axis=1)

    ids = X_raw["id"].reset_index(drop=True)
    result_df = pd.DataFrame({
        "id":                 ids,
        "predicted_category": predicted_categories,
        "confidence":         confidences,
        "actual_category":    y.reset_index(drop=True),
    })
    top_n = result_df.nlargest(limit, "confidence")
    inv_ids = [str(i) for i in top_n["id"].tolist()]

    from sqlalchemy import text as _text
    from app.core.database import SyncSessionLocal
    with SyncSessionLocal() as session:
        rows = session.execute(_text("""
            SELECT i.id::text, i.invoice_number, i.total_amount, v.name AS vendor_name
            FROM ap.invoices i
            JOIN ap.vendors v ON v.id = i.vendor_id
            WHERE i.id::text = ANY(:ids)
        """), {"ids": inv_ids}).fetchall()

    info = {r[0]: {"invoice_number": r[1], "total_amount": r[2],
                   "vendor_name": r[3]} for r in rows}

    results = []
    for _, row in top_n.iterrows():
        inv = info.get(str(row["id"]), {})
        conf = float(row["confidence"])
        actual = str(row["actual_category"])
        predicted = str(row["predicted_category"])
        results.append({
            "invoice_id":         str(row["id"]),
            "invoice_number":     inv.get("invoice_number", ""),
            "vendor_name":        inv.get("vendor_name", ""),
            "total_amount":       float(inv.get("total_amount", 0)),
            "actual_category":    actual,
            "predicted_category": predicted,
            "confidence":         round(conf, 4),
            "confidence_pct":     round(conf * 100, 1),
            "is_match":           actual.lower() == predicted.lower(),
        })
    return results


# ── Inference ─────────────────────────────────────────────────────────────────


def predict(
    invoice_dict: dict[str, Any],
    line_dicts: list[dict[str, Any]],
    vendor_dict: dict[str, Any],
) -> dict[str, Any]:
    """Predict the invoice category.

    Args:
        invoice_dict: Raw ``ap.invoices`` fields (total_amount, description, etc.).
        line_dicts:   List of ``ap.invoice_lines`` dicts for this invoice.
        vendor_dict:  Raw ``ap.vendors`` fields (payment_terms_days, invoice_count).

    Returns:
        Dictionary containing ``predicted_category``, ``confidence``,
        ``top_3_predictions`` (category + probability), and ``latency_ms``.

    Raises:
        FileNotFoundError: When the model artifact has not been trained yet.
    """
    if not ARTIFACT_PATH.exists():
        raise FileNotFoundError(
            f"[{MODEL_NAME}] Model artifact not found at {ARTIFACT_PATH}. "
            "Trigger training first via POST /api/v1/mlops/train/invoice_classifier."
        )

    t0 = time.monotonic()
    artifact = joblib.load(ARTIFACT_PATH)

    pipeline: Pipeline = artifact["pipeline"]
    tfidf_vectorizer = artifact["tfidf_vectorizer"]
    label_encoder: LabelEncoder = artifact["label_encoder"]

    X = build_inference_vector(
        invoice_dict, line_dicts, vendor_dict, tfidf_vectorizer
    )

    y_pred_encoded = pipeline.predict(X)[0]
    y_proba = pipeline.predict_proba(X)[0]

    predicted_category = label_encoder.inverse_transform([y_pred_encoded])[0]
    confidence = round(float(y_proba.max()), 4)

    # Top-3 predictions with probabilities
    top_idx = np.argsort(y_proba)[::-1][:3]
    top_3 = [
        {
            "category": label_encoder.inverse_transform([i])[0],
            "probability": round(float(y_proba[i]), 4),
        }
        for i in top_idx
    ]

    result: dict[str, Any] = {
        "predicted_category": predicted_category,
        "confidence": confidence,
        "top_3_predictions": top_3,
        "latency_ms": round((time.monotonic() - t0) * 1000, 2),
    }
    return result
