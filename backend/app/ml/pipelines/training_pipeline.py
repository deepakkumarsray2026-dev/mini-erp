"""
training_pipeline.py

Orchestrates the end-to-end training workflow for all Phase 2 ML models.

Responsibilities
----------------
1. Dispatch ``train()`` to the appropriate model module.
2. Persist training results to ``mlops.ml_models`` and ``mlops.ml_model_metrics``.
3. Mark the newly trained model as ``active`` and retire the previous version.
4. Update the ``MLTrainingJob`` record throughout its lifecycle.

All database writes use the synchronous ``SyncSessionLocal`` so this pipeline
can be called from Celery workers or direct HTTP handlers without needing an
async context.
"""
from __future__ import annotations

import traceback
from datetime import datetime, timezone
from typing import Any

from loguru import logger
from sqlalchemy.orm import Session

from app.core.database import SyncSessionLocal
from app.models.mlops import MLModel, MLModelMetric, MLTrainingJob, ModelStatus, ModelType

# ── Model dispatch map ────────────────────────────────────────────────────────

def _get_train_fn(model_type: ModelType):
    """Return the ``train()`` callable for the given ``ModelType``."""
    if model_type == ModelType.ATTRITION_PREDICTOR:
        from app.ml.models.attrition_predictor import train
    elif model_type == ModelType.EXPENSE_VIOLATION:
        from app.ml.models.expense_violation_detector import train
    elif model_type == ModelType.PAYROLL_ANOMALY:
        from app.ml.models.payroll_anomaly_detector import train
    elif model_type == ModelType.INVOICE_CLASSIFIER:
        from app.ml.models.invoice_classifier import train
    else:
        raise NotImplementedError(
            f"No training implementation for model type: {model_type.value}"
        )
    return train


# ── Public API ────────────────────────────────────────────────────────────────


def run_training(
    model_type: ModelType,
    triggered_by: str = "manual",
    job_id: str | None = None,
) -> dict[str, Any]:
    """Execute the full training workflow for a single model type.

    Args:
        model_type:    The ``ModelType`` enum value identifying which model to train.
        triggered_by:  Who/what initiated training — ``"manual"``, ``"api"``,
                       ``"celery"``, etc.
        job_id:        Optional existing ``MLTrainingJob.id`` to update.  When
                       ``None`` a new job record is created.

    Returns:
        Dictionary containing ``model_id``, ``model_type``, ``metrics``, and
        ``status`` keys.

    Raises:
        Exception: Re-raises any exception from the underlying ``train()`` function
                   after recording the failure in the job log.
    """
    with SyncSessionLocal() as db:
        job = _upsert_job(db, model_type, triggered_by, job_id)
        job_id = job.id
        db.commit()

    logger.info(f"[training_pipeline] Starting {model_type.value} | job={job_id}")

    try:
        train_fn = _get_train_fn(model_type)
        metrics = train_fn()

        with SyncSessionLocal() as db:
            model_record = _register_model(db, model_type, metrics, triggered_by)
            model_id = model_record.id
            _write_metrics(db, model_id, metrics)
            _retire_previous_models(db, model_type, exclude_id=model_id)
            _complete_job(db, job_id, model_id, success=True)
            db.commit()

        logger.info(
            f"[training_pipeline] {model_type.value} completed | "
            f"model_id={model_id}"
        )
        return {
            "model_id": model_id,
            "model_type": model_type.value,
            "metrics": metrics,
            "status": "completed",
        }

    except Exception as exc:
        tb = traceback.format_exc()
        logger.error(
            f"[training_pipeline] {model_type.value} failed | "
            f"job={job_id} | error={exc}\n{tb}"
        )
        with SyncSessionLocal() as db:
            _complete_job(db, job_id, model_id=None, success=False, error=str(exc))
            db.commit()
        raise


# ── Internal helpers ──────────────────────────────────────────────────────────


def _upsert_job(
    db: Session,
    model_type: ModelType,
    triggered_by: str,
    job_id: str | None,
) -> MLTrainingJob:
    """Create or update an ``MLTrainingJob`` row, marking it as running."""
    now = datetime.now(timezone.utc)

    if job_id:
        job = db.get(MLTrainingJob, job_id)
        if job:
            job.status = "running"
            job.started_at = now
            return job

    job = MLTrainingJob(
        model_type=model_type,
        triggered_by=triggered_by,
        status="running",
        started_at=now,
    )
    db.add(job)
    db.flush()
    return job


def _register_model(
    db: Session,
    model_type: ModelType,
    metrics: dict[str, Any],
    triggered_by: str,
) -> MLModel:
    """Insert a new ``MLModel`` row and mark it active."""
    artifact_dir_map = {
        ModelType.ATTRITION_PREDICTOR: "attrition_predictor/model.joblib",
        ModelType.EXPENSE_VIOLATION:   "expense_violation_detector/model.joblib",
        ModelType.PAYROLL_ANOMALY:     "payroll_anomaly_detector/model.joblib",
        ModelType.INVOICE_CLASSIFIER:  "invoice_classifier/model.joblib",
    }

    algorithm_map = {
        ModelType.ATTRITION_PREDICTOR: "RandomForestClassifier",
        ModelType.EXPENSE_VIOLATION:   metrics.get("algorithm", "GradientBoostingClassifier"),
        ModelType.PAYROLL_ANOMALY:     metrics.get("algorithm", "RandomForestClassifier"),
        ModelType.INVOICE_CLASSIFIER:  "RandomForestClassifier",
    }

    from app.core.config import settings
    from pathlib import Path

    artifact_path = str(
        Path(settings.MODELS_DIR) / artifact_dir_map.get(model_type, "")
    )

    model = MLModel(
        name=model_type.value,
        model_type=model_type,
        version=_next_version(db, model_type),
        status=ModelStatus.ACTIVE,
        algorithm=algorithm_map.get(model_type, "unknown"),
        artifact_path=artifact_path,
        train_rows=metrics.get("train_rows"),
        is_active=True,
        hyperparams=_extract_hyperparams(model_type),
        feature_names={"features": _get_feature_cols(model_type)},
    )
    db.add(model)
    db.flush()
    return model


def _write_metrics(
    db: Session,
    model_id: str,
    metrics: dict[str, Any],
) -> None:
    """Write an ``MLModelMetric`` row from the training metrics dict."""
    metric = MLModelMetric(
        model_id=model_id,
        split="test",
        accuracy=metrics.get("accuracy"),
        precision=metrics.get("precision") or metrics.get("precision_macro"),
        recall=metrics.get("recall") or metrics.get("recall_macro"),
        f1_score=metrics.get("f1_score") or metrics.get("f1_macro"),
        roc_auc=metrics.get("roc_auc"),
        extra={
            k: v for k, v in metrics.items()
            if k not in {"accuracy", "precision", "recall", "f1_score", "roc_auc"}
        },
    )
    db.add(metric)


def _retire_previous_models(
    db: Session,
    model_type: ModelType,
    exclude_id: str,
) -> None:
    """Set all previous active models of this type to RETIRED."""
    from sqlalchemy import update
    db.execute(
        update(MLModel)
        .where(MLModel.model_type == model_type)
        .where(MLModel.id != exclude_id)
        .where(MLModel.is_active == True)  # noqa: E712
        .values(status=ModelStatus.RETIRED, is_active=False)
    )


def _complete_job(
    db: Session,
    job_id: str,
    model_id: str | None,
    success: bool,
    error: str | None = None,
) -> None:
    """Mark the training job as completed or failed."""
    job = db.get(MLTrainingJob, job_id)
    if not job:
        return

    now = datetime.now(timezone.utc)
    job.finished_at = now
    job.status = "completed" if success else "failed"
    job.result_model_id = model_id
    if error:
        job.error_message = error[:2000]


def _next_version(db: Session, model_type: ModelType) -> str:
    """Return the next semantic version string (e.g. '1.0.0' → '2.0.0')."""
    from sqlalchemy import func, select
    count = db.scalar(
        select(func.count()).select_from(MLModel).where(MLModel.model_type == model_type)
    ) or 0
    return f"{count + 1}.0.0"


def _extract_hyperparams(model_type: ModelType) -> dict[str, Any]:
    """Return the key hyperparameters for documentation purposes."""
    return {
        ModelType.ATTRITION_PREDICTOR: {
            "n_estimators": 200, "max_depth": 8, "class_weight": "balanced",
        },
        ModelType.EXPENSE_VIOLATION: {
            "n_estimators": 200, "learning_rate": 0.05, "max_depth": 4,
        },
        ModelType.PAYROLL_ANOMALY: {
            "n_estimators": 300, "max_depth": 10, "class_weight": "balanced",
        },
        ModelType.INVOICE_CLASSIFIER: {
            "n_estimators": 300, "max_depth": 12, "class_weight": "balanced",
            "tfidf_max_features": 50,
        },
    }.get(model_type, {})


def _get_feature_cols(model_type: ModelType) -> list[str]:
    """Return the feature column list for the given model type."""
    if model_type == ModelType.ATTRITION_PREDICTOR:
        from app.ml.features.employee_features import FEATURE_COLS
    elif model_type == ModelType.EXPENSE_VIOLATION:
        from app.ml.features.expense_features import FEATURE_COLS
    elif model_type == ModelType.PAYROLL_ANOMALY:
        from app.ml.features.payroll_features import FEATURE_COLS
    elif model_type == ModelType.INVOICE_CLASSIFIER:
        from app.ml.features.invoice_features import NUMERIC_FEATURE_COLS as FEATURE_COLS
    else:
        return []
    return list(FEATURE_COLS)
