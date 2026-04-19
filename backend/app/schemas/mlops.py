"""
schemas/mlops.py

Pydantic request and response models for the MLOps API.

Schema families
---------------
- ``MLModelResponse``         — model registry entry
- ``MLModelMetricResponse``   — per-model evaluation metrics
- ``MLPredictionLogResponse`` — audit log of inference calls
- ``MLTrainingJobResponse``   — training job lifecycle record
- ``TrainRequest``            — optional body for POST /train/{model_type}
- Prediction request schemas  — one per model type
- Prediction response schemas — one per model type
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Shared sub-models ─────────────────────────────────────────────────────────


class FeatureImportanceItem(BaseModel):
    feature: str
    importance: float = Field(..., ge=0.0, le=1.0)


class Top3Prediction(BaseModel):
    category: str
    probability: float = Field(..., ge=0.0, le=1.0)


# ── Model registry ────────────────────────────────────────────────────────────


class MLModelMetricResponse(BaseModel):
    id: str
    model_id: str
    split: str
    accuracy: float | None
    precision: float | None
    recall: float | None
    f1_score: float | None
    roc_auc: float | None
    mse: float | None
    mae: float | None
    extra: dict[str, Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MLModelResponse(BaseModel):
    id: str
    name: str
    model_type: str
    version: str
    status: str
    algorithm: str | None
    artifact_path: str | None
    train_rows: int | None
    is_active: bool
    hyperparams: dict[str, Any] | None
    feature_names: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
    metrics: list[MLModelMetricResponse] = []

    model_config = {"from_attributes": True}


# ── Training jobs ─────────────────────────────────────────────────────────────


class TrainRequest(BaseModel):
    """Optional request body for POST /train/{model_type}."""

    triggered_by: str = Field(
        default="api",
        description="Who or what initiated this training run.",
        examples=["api", "scheduled_job", "data_refresh"],
    )


class TrainResponse(BaseModel):
    model_id: str
    model_type: str
    status: str
    metrics: dict[str, Any]


class MLTrainingJobResponse(BaseModel):
    id: str
    model_type: str
    triggered_by: str
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    result_model_id: str | None
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Prediction logs ───────────────────────────────────────────────────────────


class MLPredictionLogResponse(BaseModel):
    id: str
    model_id: str
    entity_type: str
    entity_id: str
    prediction: str
    probability: float | None
    explanation: dict[str, Any] | None
    latency_ms: int | None
    predicted_at: datetime

    model_config = {"from_attributes": True}


# ── Attrition prediction ──────────────────────────────────────────────────────


class AttritionPredictResponse(BaseModel):
    employee_id: str
    prediction: str = Field(..., description="'high_risk' or 'low_risk'")
    probability: float = Field(..., ge=0.0, le=1.0)
    risk_score: float = Field(..., ge=0.0, le=1.0)
    top_features: list[FeatureImportanceItem]
    latency_ms: float


# ── Expense violation prediction ──────────────────────────────────────────────


class ExpenseViolationPredictResponse(BaseModel):
    expense_line_id: str
    prediction: str = Field(..., description="'violation' or 'compliant'")
    is_violation: bool
    probability: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    top_features: list[FeatureImportanceItem] | None = None
    anomaly_score: float | None = None
    model_mode: str
    latency_ms: float


# ── Payroll anomaly prediction ────────────────────────────────────────────────


class PayrollAnomalyPredictResponse(BaseModel):
    payslip_id: str
    prediction: str = Field(..., description="'anomalous' or 'normal'")
    is_anomalous: bool
    probability: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    top_features: list[FeatureImportanceItem] | None = None
    anomaly_score: float | None = None
    model_mode: str
    latency_ms: float


# ── Invoice classification prediction ────────────────────────────────────────


class InvoiceClassifyResponse(BaseModel):
    invoice_id: str
    predicted_category: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    top_3_predictions: list[Top3Prediction]
    latency_ms: float
