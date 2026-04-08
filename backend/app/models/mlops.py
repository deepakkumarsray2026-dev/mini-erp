import enum
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ModelStatus(str, enum.Enum):
    TRAINING   = "training"
    TRAINED    = "trained"
    EVALUATING = "evaluating"
    ACTIVE     = "active"
    RETIRED    = "retired"
    FAILED     = "failed"


class ModelType(str, enum.Enum):
    ATTRITION_PREDICTOR      = "attrition_predictor"
    EXPENSE_VIOLATION        = "expense_violation"
    PAYROLL_ANOMALY          = "payroll_anomaly"
    INVOICE_CLASSIFIER       = "invoice_classifier"
    BUDGET_FORECASTER        = "budget_forecaster"
    INVOICE_IMAGE_CLASSIFIER = "invoice_image_classifier"


class MLModel(Base, TimestampMixin):
    """Registry of all trained ML models."""
    __tablename__ = "ml_models"
    __table_args__ = {"schema": "mlops"}

    id:            Mapped[str]        = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    name:          Mapped[str]        = mapped_column(String(100), nullable=False)
    model_type:    Mapped[ModelType]  = mapped_column(Enum(ModelType), nullable=False)
    version:       Mapped[str]        = mapped_column(String(20), nullable=False, default="1.0.0")
    status:        Mapped[ModelStatus]= mapped_column(Enum(ModelStatus), default=ModelStatus.TRAINING)
    algorithm:     Mapped[str]        = mapped_column(String(100))
    artifact_path: Mapped[str|None]   = mapped_column(String(500))
    mlflow_run_id: Mapped[str|None]   = mapped_column(String(100))
    hyperparams:   Mapped[dict|None]  = mapped_column(JSONB)
    feature_names: Mapped[dict|None]  = mapped_column(JSONB)
    train_rows:    Mapped[int|None]   = mapped_column(Integer)
    is_active:     Mapped[bool]       = mapped_column(Boolean, default=False)

    metrics:     Mapped[list["MLModelMetric"]]   = relationship("MLModelMetric", back_populates="model", cascade="all, delete-orphan")
    predictions: Mapped[list["MLPredictionLog"]] = relationship("MLPredictionLog", back_populates="model")


class MLModelMetric(Base, TimestampMixin):
    """Evaluation metrics for each trained model."""
    __tablename__ = "ml_model_metrics"
    __table_args__ = {"schema": "mlops"}

    id:        Mapped[str]        = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    model_id:  Mapped[str]        = mapped_column(UUID(as_uuid=False), ForeignKey("mlops.ml_models.id"), nullable=False)
    split:     Mapped[str]        = mapped_column(String(10), default="test")
    accuracy:  Mapped[float|None] = mapped_column(Float)
    precision: Mapped[float|None] = mapped_column(Float)
    recall:    Mapped[float|None] = mapped_column(Float)
    f1_score:  Mapped[float|None] = mapped_column(Float)
    roc_auc:   Mapped[float|None] = mapped_column(Float)
    mse:       Mapped[float|None] = mapped_column(Float)
    mae:       Mapped[float|None] = mapped_column(Float)
    extra:     Mapped[dict|None]  = mapped_column(JSONB)

    model: Mapped[MLModel] = relationship("MLModel", back_populates="metrics")


class MLPredictionLog(Base):
    """Log of every inference call for audit and drift detection."""
    __tablename__ = "ml_prediction_logs"
    __table_args__ = {"schema": "mlops"}

    id:           Mapped[str]       = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    model_id:     Mapped[str]       = mapped_column(UUID(as_uuid=False), ForeignKey("mlops.ml_models.id"), nullable=False)
    entity_type:  Mapped[str]       = mapped_column(String(50))
    entity_id:    Mapped[str]       = mapped_column(String(100))
    input_data:   Mapped[dict|None] = mapped_column(JSONB)
    prediction:   Mapped[str]       = mapped_column(String(100))
    probability:  Mapped[float|None]= mapped_column(Float)
    explanation:  Mapped[dict|None] = mapped_column(JSONB)
    predicted_at: Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())
    latency_ms:   Mapped[int|None]  = mapped_column(Integer)

    model: Mapped[MLModel] = relationship("MLModel", back_populates="predictions")


class MLTrainingJob(Base, TimestampMixin):
    """Tracks training job runs."""
    __tablename__ = "ml_training_jobs"
    __table_args__ = {"schema": "mlops"}

    id:              Mapped[str]       = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    model_type:      Mapped[ModelType] = mapped_column(Enum(ModelType), nullable=False)
    triggered_by:    Mapped[str]       = mapped_column(String(50), default="manual")
    status:          Mapped[str]       = mapped_column(String(20), default="queued")
    started_at:      Mapped[datetime|None] = mapped_column(DateTime(timezone=True))
    finished_at:     Mapped[datetime|None] = mapped_column(DateTime(timezone=True))
    result_model_id: Mapped[str|None]  = mapped_column(UUID(as_uuid=False), ForeignKey("mlops.ml_models.id"))
    error_message:   Mapped[str|None]  = mapped_column(Text)
    logs:            Mapped[dict|None] = mapped_column(JSONB)
