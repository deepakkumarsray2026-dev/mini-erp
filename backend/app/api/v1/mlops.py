"""
mlops.py

MLOps API — model training, inference, registry, and audit log.

Endpoints
---------
POST   /train/{model_type}                  Trigger training for a model
GET    /models                              List all registered models
GET    /models/{model_id}                   Model detail with metrics
POST   /predict/attrition/{employee_id}     Attrition risk prediction
POST   /predict/expense-violation/{line_id} Expense policy violation prediction
POST   /predict/payroll-anomaly/{payslip_id}Payroll anomaly detection
POST   /predict/invoice/{invoice_id}        Invoice category classification
GET    /predictions                         Prediction audit log
GET    /jobs                                Training job history

Security
--------
All endpoints require authentication.  Training and predict endpoints also
require the ``ai:run`` permission.  Read-only endpoints (models, predictions,
jobs) require ``ai:read``.
"""
from __future__ import annotations

import asyncio
from functools import partial
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.permissions import ModuleName, can_read, can_run
from app.models.mlops import (
    MLModel,
    MLPredictionLog,
    MLTrainingJob,
    ModelType,
)
from app.schemas.common import PaginatedResponse, paginate
from app.schemas.mlops import (
    AttritionPredictResponse,
    ExpenseViolationPredictResponse,
    InvoiceClassifyResponse,
    MLModelResponse,
    MLPredictionLogResponse,
    MLTrainingJobResponse,
    PayrollAnomalyPredictResponse,
    TrainRequest,
    TrainResponse,
)

router = APIRouter()

# ── Helpers ───────────────────────────────────────────────────────────────────

_MODEL_TYPE_MAP: dict[str, ModelType] = {mt.value: mt for mt in ModelType}


def _resolve_model_type(model_type_str: str) -> ModelType:
    """Parse a URL path segment into a ``ModelType`` enum value."""
    mt = _MODEL_TYPE_MAP.get(model_type_str)
    if mt is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Unknown model_type '{model_type_str}'. "
                f"Valid values: {list(_MODEL_TYPE_MAP.keys())}"
            ),
        )
    return mt


async def _run_in_thread(fn, *args, **kwargs):
    """Execute a synchronous callable in a thread pool to avoid blocking the event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(fn, *args, **kwargs))


def _not_found(artifact: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=artifact,
    )


def _model_not_trained(model_type: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=(
            f"No trained model found for '{model_type}'. "
            f"Train it first: POST /api/v1/mlops/train/{model_type}"
        ),
    )


# ── Training ──────────────────────────────────────────────────────────────────


@router.post(
    "/train/{model_type}",
    response_model=TrainResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Train a model",
    description=(
        "Trigger training for the specified model type. "
        "Training runs synchronously in a thread pool. "
        "Valid model_type values: `attrition_predictor`, `expense_violation`, "
        "`payroll_anomaly`, `invoice_classifier`."
    ),
)
async def train_model(
    model_type: str,
    body: TrainRequest = TrainRequest(),
    _=Depends(can_run(ModuleName.AI)),
):
    mt = _resolve_model_type(model_type)
    logger.info(f"[mlops] Training requested | model={model_type} | by={body.triggered_by}")

    try:
        from app.ml.pipelines.training_pipeline import run_training
        result = await _run_in_thread(
            run_training,
            mt,
            body.triggered_by,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except NotImplementedError as exc:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(exc))
    except Exception as exc:
        logger.error(f"[mlops] Training failed | model={model_type} | error={exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Training failed: {exc}",
        )

    return result


# ── Model registry ────────────────────────────────────────────────────────────


@router.get(
    "/models",
    response_model=PaginatedResponse[MLModelResponse],
    summary="List all registered models",
)
async def list_models(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    model_type: str | None = Query(None, description="Filter by model type"),
    active_only: bool = Query(False, description="Return only active models"),
    _=Depends(can_read(ModuleName.AI)),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(MLModel)
        .options(selectinload(MLModel.metrics))
        .order_by(MLModel.created_at.desc())
    )
    if model_type:
        mt = _resolve_model_type(model_type)
        stmt = stmt.where(MLModel.model_type == mt)
    if active_only:
        stmt = stmt.where(MLModel.is_active == True)  # noqa: E712

    result = await db.execute(stmt)
    models = result.scalars().all()

    offset = (page - 1) * page_size
    page_items = models[offset : offset + page_size]
    return paginate(page_items, len(models), page, page_size)


@router.get(
    "/models/{model_id}",
    response_model=MLModelResponse,
    summary="Get model details",
)
async def get_model(
    model_id: str,
    _=Depends(can_read(ModuleName.AI)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MLModel)
        .where(MLModel.id == model_id)
        .options(selectinload(MLModel.metrics))
    )
    model = result.scalar_one_or_none()
    if not model:
        raise _not_found(f"Model '{model_id}' not found.")
    return model


# ── Predictions ───────────────────────────────────────────────────────────────


@router.post(
    "/predict/attrition/{employee_id}",
    response_model=AttritionPredictResponse,
    summary="Predict attrition risk for an employee",
)
async def predict_attrition(
    employee_id: str,
    _=Depends(can_run(ModuleName.AI)),
    db: AsyncSession = Depends(get_db),
):
    from app.models.hcm import Employee

    result = await db.execute(
        select(Employee)
        .where(Employee.id == employee_id)
        .options(selectinload(Employee.job))
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise _not_found(f"Employee '{employee_id}' not found.")

    employee_dict = _employee_to_dict(employee)

    try:
        from app.ml.models.attrition_predictor import predict
        pred = await _run_in_thread(predict, employee_dict)
    except FileNotFoundError:
        raise _model_not_trained("attrition_predictor")
    except Exception as exc:
        logger.error(f"[mlops] Attrition predict error | employee={employee_id} | {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

    asyncio.get_event_loop().run_in_executor(
        None,
        _log_prediction_sync,
        ModelType.ATTRITION_PREDICTOR,
        "employee",
        employee_id,
        employee_dict,
        pred,
    )

    return AttritionPredictResponse(
        employee_id=employee_id,
        **pred,
    )


@router.post(
    "/predict/expense-violation/{line_id}",
    response_model=ExpenseViolationPredictResponse,
    summary="Predict whether an expense line is a policy violation",
)
async def predict_expense_violation(
    line_id: str,
    _=Depends(can_run(ModuleName.AI)),
    db: AsyncSession = Depends(get_db),
):
    from app.models.expenses import ExpenseLine, ExpenseReport, ExpenseCategory

    line_result = await db.execute(
        select(ExpenseLine)
        .where(ExpenseLine.id == line_id)
        .options(
            selectinload(ExpenseLine.report).selectinload(ExpenseReport.employee),
            selectinload(ExpenseLine.category),
        )
    )
    line = line_result.scalar_one_or_none()
    if not line:
        raise _not_found(f"ExpenseLine '{line_id}' not found.")

    line_dict = _expense_line_to_dict(line)
    employee_dict = _employee_to_dict(line.report.employee)
    category_dict = _expense_category_to_dict(line.category)

    try:
        from app.ml.models.expense_violation_detector import predict
        pred = await _run_in_thread(predict, line_dict, employee_dict, category_dict)
    except FileNotFoundError:
        raise _model_not_trained("expense_violation")
    except Exception as exc:
        logger.error(f"[mlops] Expense violation predict error | line={line_id} | {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

    asyncio.get_event_loop().run_in_executor(
        None,
        _log_prediction_sync,
        ModelType.EXPENSE_VIOLATION,
        "expense_line",
        line_id,
        line_dict,
        pred,
    )

    return ExpenseViolationPredictResponse(
        expense_line_id=line_id,
        **pred,
    )


@router.post(
    "/predict/payroll-anomaly/{payslip_id}",
    response_model=PayrollAnomalyPredictResponse,
    summary="Detect anomalies in a payslip",
)
async def predict_payroll_anomaly(
    payslip_id: str,
    _=Depends(can_run(ModuleName.AI)),
    db: AsyncSession = Depends(get_db),
):
    from app.models.payroll import PaySlip, PayrollRun, PayPeriod

    ps_result = await db.execute(
        select(PaySlip)
        .where(PaySlip.id == payslip_id)
        .options(
            selectinload(PaySlip.employee),
            selectinload(PaySlip.payroll_run).selectinload(PayrollRun.pay_period),
        )
    )
    payslip = ps_result.scalar_one_or_none()
    if not payslip:
        raise _not_found(f"Payslip '{payslip_id}' not found.")

    # Fetch previous payslip gross pay for delta feature
    prev_result = await db.execute(
        select(PaySlip.gross_pay)
        .join(PayrollRun, PayrollRun.id == PaySlip.payroll_run_id)
        .join(PayPeriod, PayPeriod.id == PayrollRun.pay_period_id)
        .where(PaySlip.employee_id == payslip.employee_id)
        .where(PaySlip.id != payslip_id)
        .order_by(PayPeriod.start_date.desc())
        .limit(1)
    )
    prev_gross_row = prev_result.scalar_one_or_none()
    prev_gross = float(prev_gross_row) if prev_gross_row is not None else None

    payslip_dict = _payslip_to_dict(payslip)
    employee_dict = _employee_to_dict(payslip.employee)

    try:
        from app.ml.models.payroll_anomaly_detector import predict
        pred = await _run_in_thread(predict, payslip_dict, employee_dict, prev_gross)
    except FileNotFoundError:
        raise _model_not_trained("payroll_anomaly")
    except Exception as exc:
        logger.error(f"[mlops] Payroll anomaly predict error | payslip={payslip_id} | {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

    asyncio.get_event_loop().run_in_executor(
        None,
        _log_prediction_sync,
        ModelType.PAYROLL_ANOMALY,
        "payslip",
        payslip_id,
        payslip_dict,
        pred,
    )

    return PayrollAnomalyPredictResponse(
        payslip_id=payslip_id,
        **pred,
    )


@router.post(
    "/predict/invoice/{invoice_id}",
    response_model=InvoiceClassifyResponse,
    summary="Classify an invoice into a spend category",
)
async def predict_invoice_category(
    invoice_id: str,
    _=Depends(can_run(ModuleName.AI)),
    db: AsyncSession = Depends(get_db),
):
    from app.models.ap import Invoice, Vendor

    inv_result = await db.execute(
        select(Invoice)
        .where(Invoice.id == invoice_id)
        .options(
            selectinload(Invoice.lines),
            selectinload(Invoice.vendor),
        )
    )
    invoice = inv_result.scalar_one_or_none()
    if not invoice:
        raise _not_found(f"Invoice '{invoice_id}' not found.")

    invoice_dict = _invoice_to_dict(invoice)
    line_dicts = [_invoice_line_to_dict(line) for line in invoice.lines]
    vendor_dict = _vendor_to_dict(invoice.vendor)

    try:
        from app.ml.models.invoice_classifier import predict
        pred = await _run_in_thread(predict, invoice_dict, line_dicts, vendor_dict)
    except FileNotFoundError:
        raise _model_not_trained("invoice_classifier")
    except Exception as exc:
        logger.error(f"[mlops] Invoice classify error | invoice={invoice_id} | {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

    asyncio.get_event_loop().run_in_executor(
        None,
        _log_prediction_sync,
        ModelType.INVOICE_CLASSIFIER,
        "invoice",
        invoice_id,
        invoice_dict,
        pred,
    )

    return InvoiceClassifyResponse(
        invoice_id=invoice_id,
        **pred,
    )


# ── Batch insights ────────────────────────────────────────────────────────────


@router.get(
    "/insights/attrition-risk",
    summary="Top N active employees by attrition risk",
    response_model=list[dict],
)
async def attrition_risk_insight(
    limit: int = Query(10, ge=1, le=500),
    _=Depends(can_read(ModuleName.AI)),
):
    try:
        from app.ml.models.attrition_predictor import predict_all_active
        return await _run_in_thread(predict_all_active, limit)
    except FileNotFoundError:
        raise _model_not_trained("attrition_predictor")
    except Exception as exc:
        logger.error(f"[mlops] attrition insight error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/insights/expense-violations",
    summary="Top N expense lines by violation probability",
    response_model=list[dict],
)
async def expense_violation_insight(
    limit: int = Query(10, ge=1, le=500),
    _=Depends(can_read(ModuleName.AI)),
):
    try:
        from app.ml.models.expense_violation_detector import predict_all_top
        return await _run_in_thread(predict_all_top, limit)
    except FileNotFoundError:
        raise _model_not_trained("expense_violation")
    except Exception as exc:
        logger.error(f"[mlops] expense insight error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/insights/invoice-classifications",
    summary="Top N invoices by classification confidence",
    response_model=list[dict],
)
async def invoice_classification_insight(
    limit: int = Query(10, ge=1, le=500),
    _=Depends(can_read(ModuleName.AI)),
):
    try:
        from app.ml.models.invoice_classifier import predict_all_top
        return await _run_in_thread(predict_all_top, limit)
    except FileNotFoundError:
        raise _model_not_trained("invoice_classifier")
    except Exception as exc:
        logger.error(f"[mlops] invoice insight error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/insights/payroll-anomalies",
    summary="Top N payslips by anomaly probability",
    response_model=list[dict],
)
async def payroll_anomaly_insight(
    limit: int = Query(10, ge=1, le=500),
    _=Depends(can_read(ModuleName.AI)),
):
    try:
        from app.ml.models.payroll_anomaly_detector import predict_all_top
        return await _run_in_thread(predict_all_top, limit)
    except FileNotFoundError:
        raise _model_not_trained("payroll_anomaly")
    except Exception as exc:
        logger.error(f"[mlops] payroll anomaly insight error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ── Audit log & jobs ──────────────────────────────────────────────────────────


@router.get(
    "/predictions",
    response_model=PaginatedResponse[MLPredictionLogResponse],
    summary="Prediction audit log",
)
async def list_predictions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    entity_type: str | None = Query(None),
    model_type: str | None = Query(None),
    _=Depends(can_read(ModuleName.AI)),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(MLPredictionLog)
        .order_by(MLPredictionLog.predicted_at.desc())
    )
    if entity_type:
        stmt = stmt.where(MLPredictionLog.entity_type == entity_type)
    if model_type:
        mt = _resolve_model_type(model_type)
        stmt = stmt.join(MLModel, MLModel.id == MLPredictionLog.model_id).where(
            MLModel.model_type == mt
        )

    result = await db.execute(stmt)
    logs = result.scalars().all()

    offset = (page - 1) * page_size
    return paginate(logs[offset : offset + page_size], len(logs), page, page_size)


@router.get(
    "/jobs",
    response_model=PaginatedResponse[MLTrainingJobResponse],
    summary="Training job history",
)
async def list_training_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    model_type: str | None = Query(None),
    _=Depends(can_read(ModuleName.AI)),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(MLTrainingJob).order_by(MLTrainingJob.created_at.desc())
    if model_type:
        mt = _resolve_model_type(model_type)
        stmt = stmt.where(MLTrainingJob.model_type == mt)

    result = await db.execute(stmt)
    jobs = result.scalars().all()

    offset = (page - 1) * page_size
    return paginate(jobs[offset : offset + page_size], len(jobs), page, page_size)


# ── Entity → dict helpers ─────────────────────────────────────────────────────
# These extract raw field values from ORM objects without leaking ORM internals
# into the ML layer.


def _employee_to_dict(employee) -> dict[str, Any]:
    return {
        "hire_date": employee.hire_date,
        "date_of_birth": employee.date_of_birth,
        "satisfaction_score": employee.satisfaction_score,
        "performance_rating": employee.performance_rating,
        "overtime_monthly_avg": employee.overtime_monthly_avg,
        "training_hours_ytd": employee.training_hours_ytd,
        "base_salary": employee.base_salary,
        "employment_type": employee.employment_type,
        "employment_status": employee.employment_status,
        "manager_id": employee.manager_id,
        "salary_max": getattr(getattr(employee, "job", None), "salary_max", None),
        "dept_headcount": 10,  # default; overridden by feature SQL when training
    }


def _expense_line_to_dict(line) -> dict[str, Any]:
    return {
        "amount": line.amount,
        "expense_date": line.expense_date,
        "receipt_path": line.receipt_path,
        "is_billable": line.is_billable,
        "is_violation": line.is_violation,
        "category_id": line.category_id,
    }


def _expense_category_to_dict(category) -> dict[str, Any]:
    return {
        "daily_limit": category.daily_limit,
        "encoded": 0,  # default encoding; training uses a fit encoder
    }


def _payslip_to_dict(payslip) -> dict[str, Any]:
    return {
        "gross_pay": payslip.gross_pay,
        "net_pay": payslip.net_pay,
        "income_tax": payslip.income_tax,
        "employee_ni": payslip.employee_ni,
        "employee_pension": payslip.employee_pension,
        "total_deductions": payslip.total_deductions,
        "is_anomalous": payslip.is_anomalous,
    }


def _invoice_to_dict(invoice) -> dict[str, Any]:
    return {
        "total_amount": invoice.total_amount,
        "tax_amount": invoice.tax_amount,
        "description": invoice.description,
        "category": invoice.category,
        "invoice_date": invoice.invoice_date,
        "due_date": invoice.due_date,
    }


def _invoice_line_to_dict(line) -> dict[str, Any]:
    return {"amount": line.amount, "description": line.description}


def _vendor_to_dict(vendor) -> dict[str, Any]:
    return {
        "payment_terms_days": vendor.payment_terms_days,
        "invoice_count": 1,  # approximate; exact count from SQL during training
    }


# ── Fire-and-forget prediction logger ────────────────────────────────────────


def _log_prediction_sync(model_type, entity_type, entity_id, input_data, result):
    """Synchronous wrapper around ``inference_pipeline.log_prediction``."""
    try:
        from app.ml.pipelines.inference_pipeline import log_prediction
        log_prediction(model_type, entity_type, entity_id, input_data, result)
    except Exception as exc:
        logger.warning(f"[mlops] Prediction log failed silently: {exc}")
