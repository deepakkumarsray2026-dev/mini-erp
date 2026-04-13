from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class PurchaseRequisition(Base, TimestampMixin):
    __tablename__ = "purchase_requisitions"
    __table_args__ = {"schema": "procurement"}

    id:            Mapped[str]          = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    pr_number:     Mapped[str]          = mapped_column(String(30), unique=True, nullable=False)
    requested_by:  Mapped[str]          = mapped_column(UUID(as_uuid=False), ForeignKey("hcm.employees.id"))
    department_id: Mapped[str]          = mapped_column(UUID(as_uuid=False), ForeignKey("hcm.departments.id"))
    title:         Mapped[str]          = mapped_column(String(200), nullable=False)
    justification: Mapped[str|None]     = mapped_column(Text)
    required_date: Mapped[date|None]    = mapped_column(Date)
    total_amount:  Mapped[Decimal]      = mapped_column(Numeric(15, 2), default=0)
    currency:      Mapped[str]          = mapped_column(String(3), default="GBP")
    status:        Mapped[str]          = mapped_column(String(20), default="draft")
    approved_by:   Mapped[str|None]     = mapped_column(UUID(as_uuid=False))

    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship("PurchaseOrder", back_populates="requisition")
    requester: Mapped["Employee"] = relationship("Employee", foreign_keys=[requested_by], primaryjoin="PurchaseRequisition.requested_by == Employee.id")


class PurchaseOrder(Base, TimestampMixin):
    __tablename__ = "purchase_orders"
    __table_args__ = {"schema": "procurement"}

    id:                Mapped[str]          = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    po_number:         Mapped[str]          = mapped_column(String(30), unique=True, nullable=False)
    requisition_id:    Mapped[str|None]     = mapped_column(UUID(as_uuid=False), ForeignKey("procurement.purchase_requisitions.id"))
    vendor_id:         Mapped[str]          = mapped_column(UUID(as_uuid=False), ForeignKey("ap.vendors.id"), nullable=False)
    issued_date:       Mapped[date]         = mapped_column(Date, nullable=False)
    expected_delivery: Mapped[date|None]    = mapped_column(Date)
    total_amount:      Mapped[Decimal]      = mapped_column(Numeric(15, 2), nullable=False)
    currency:          Mapped[str]          = mapped_column(String(3), default="GBP")
    status:            Mapped[str]          = mapped_column(String(20), default="draft")
    terms:             Mapped[str|None]     = mapped_column(Text)
    approved_by:       Mapped[str|None]     = mapped_column(UUID(as_uuid=False))

    requisition: Mapped[PurchaseRequisition|None] = relationship("PurchaseRequisition", back_populates="purchase_orders")
    vendor: Mapped["Vendor"] = relationship("Vendor", foreign_keys=[vendor_id], primaryjoin="PurchaseOrder.vendor_id == Vendor.id")
    lines:       Mapped[list["POLine"]]           = relationship("POLine", back_populates="purchase_order", cascade="all, delete-orphan")
    receipts:    Mapped[list["GoodsReceipt"]]     = relationship("GoodsReceipt", back_populates="purchase_order")


class POLine(Base, TimestampMixin):
    __tablename__ = "po_lines"
    __table_args__ = {"schema": "procurement"}

    id:                Mapped[str]     = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    po_id:             Mapped[str]     = mapped_column(UUID(as_uuid=False), ForeignKey("procurement.purchase_orders.id"), nullable=False)
    line_number:       Mapped[int]     = mapped_column(Integer, nullable=False)
    item_code:         Mapped[str|None]= mapped_column(String(50))
    description:       Mapped[str]     = mapped_column(Text, nullable=False)
    quantity:          Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    unit_of_measure:   Mapped[str]     = mapped_column(String(20), default="EA")
    unit_price:        Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    amount:            Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    gl_account_code:   Mapped[str|None]= mapped_column(String(20))
    received_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0)

    purchase_order: Mapped[PurchaseOrder] = relationship("PurchaseOrder", back_populates="lines")


class GoodsReceipt(Base, TimestampMixin):
    __tablename__ = "goods_receipts"
    __table_args__ = {"schema": "procurement"}

    id:             Mapped[str]      = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    receipt_number: Mapped[str]      = mapped_column(String(30), unique=True, nullable=False)
    po_id:          Mapped[str]      = mapped_column(UUID(as_uuid=False), ForeignKey("procurement.purchase_orders.id"), nullable=False)
    received_by:    Mapped[str]      = mapped_column(UUID(as_uuid=False), ForeignKey("hcm.employees.id"))
    receipt_date:   Mapped[date]     = mapped_column(Date, nullable=False)
    notes:          Mapped[str|None] = mapped_column(Text)

    purchase_order: Mapped[PurchaseOrder] = relationship("PurchaseOrder", back_populates="receipts")
