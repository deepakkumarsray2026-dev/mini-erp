"""
inference_pipeline.py

Thin orchestration layer that wraps each model's ``predict()`` call, logs the
result to ``mlops.ml_prediction_logs``, and surfaces a uniform response shape
to the API layer.

Design choices
--------------
- Uses ``SyncSessionLocal`` so inference can be triggered from either async
  FastAPI handlers (via ``asyncio.get_event_loop().run_in_executor``) or sync
  Celery tasks.
- Latency is measured end-to-end including DB I/O for the log write.
- The active model's ``id`` is looked up once per call; callers may pass a
  pre-resolved ``model_id`` to skip the lookup.
"""
from __future__ import annotations

import time
from typing import Any

from loguru import logger
from sqlalchemy import select

from app.core.database import SyncSessionLocal
from app.models.mlops import MLModel, MLPredictionLog, ModelType


# ── Public helpers ────────────────────────────────────────────────────────────


def log_prediction(
    model_type: ModelType,
    entity_type: str,
    entity_id: str,
    input_data: dict[str, Any],
    result: dict[str, Any],
    model_id: str | None = None,
) -> None:
    """Persist a prediction result to ``mlops.ml_prediction_logs``.

    Args:
        model_type:   The ``ModelType`` of the model that produced the result.
        entity_type:  Human-readable entity type tag (e.g. ``"employee"``,
                      ``"payslip"``, ``"invoice"``).
        entity_id:    The primary key of the entity that was scored.
        input_data:   The feature/request dict passed to the model.
        result:       The prediction dict returned by the model.
        model_id:     Pre-resolved active model ID.  When ``None`` the active
                      model is looked up from the database.
    """
    t0 = time.monotonic()

    try:
        with SyncSessionLocal() as db:
            resolved_model_id = model_id or _resolve_active_model_id(db, model_type)
            if not resolved_model_id:
                logger.warning(
                    f"[inference_pipeline] No active model found for "
                    f"{model_type.value} — skipping prediction log."
                )
                return

            log = MLPredictionLog(
                model_id=resolved_model_id,
                entity_type=entity_type,
                entity_id=str(entity_id),
                input_data=_sanitise_input(input_data),
                prediction=str(result.get("prediction", result.get("predicted_category", ""))),
                probability=result.get("probability") or result.get("confidence"),
                explanation={
                    k: v for k, v in result.items()
                    if k not in {"prediction", "predicted_category", "probability",
                                 "confidence", "latency_ms"}
                },
                latency_ms=int(result.get("latency_ms", 0)),
            )
            db.add(log)
            db.commit()

    except Exception as exc:
        # Prediction logging is non-critical — never let it break the caller.
        logger.error(
            f"[inference_pipeline] Failed to log prediction for "
            f"{model_type.value}/{entity_id}: {exc}"
        )

    logger.debug(
        f"[inference_pipeline] Logged {model_type.value} prediction for "
        f"{entity_type}={entity_id} in {(time.monotonic() - t0) * 1000:.1f}ms"
    )


def get_active_model_id(model_type: ModelType) -> str | None:
    """Return the ``id`` of the currently active model, or ``None``."""
    with SyncSessionLocal() as db:
        return _resolve_active_model_id(db, model_type)


# ── Internal helpers ──────────────────────────────────────────────────────────


def _resolve_active_model_id(db, model_type: ModelType) -> str | None:
    row = db.scalar(
        select(MLModel.id)
        .where(MLModel.model_type == model_type)
        .where(MLModel.is_active == True)  # noqa: E712
        .order_by(MLModel.created_at.desc())
        .limit(1)
    )
    return row


def _sanitise_input(data: dict[str, Any]) -> dict[str, Any]:
    """Strip any keys whose values are not JSON-serialisable.

    Handles date objects, Decimal, and other common non-serialisable types by
    converting them to strings.
    """
    import datetime
    from decimal import Decimal

    sanitised: dict[str, Any] = {}
    for k, v in data.items():
        if isinstance(v, (datetime.date, datetime.datetime)):
            sanitised[k] = v.isoformat()
        elif isinstance(v, Decimal):
            sanitised[k] = float(v)
        elif isinstance(v, (str, int, float, bool, type(None))):
            sanitised[k] = v
        else:
            sanitised[k] = str(v)
    return sanitised
