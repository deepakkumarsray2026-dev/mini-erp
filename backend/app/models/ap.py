import enum
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class VendorStatus(str, enum.Enum):
    ACTIVE           = "active"
    INACTIVE         = "inactive"
    BLOCKED          = "blocked"
    PENDING_APPROVAL = "pending_approval"


class InvoiceStatus(str, enum.Enum):
    DRAFT        = "draft"
    SUBMITTED    = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED     = "approved"
    REJECTED     = "rejected"
    MATCHED      = "matched"
    POSTED       = "posted"
    PAID         = "paid"
    CANCELLED    = "cancelled"


class Vendor(Base, TimestampMixin):
    __tablename__ = "vendors"
    __table_args__ = {"schema": "ap"}

    id:                  Mapped[str]          = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    vendor_id:           Mapped[str]          = mapped_column(String(20), unique=True, nullable=False)
    name:                Mapped[str]          = mapped_column(String(200), nullable=False)
    legal_name:          Mapped[str|None]     = mapped_column(String(200))
    tax_id:              Mapped[str|None]     = mapped_column(String(50))
    vat_number:          Mapped[str|None]     = mapped_column(String(30))
    email:               Mapped[str|None]     = mapped_column(String(150))
    phone:               Mapped[str|None]     = mapped_column(String(30))
    address_line1:       Mapped[str|None]     = mapped_column(String(200))
    city:                Mapped[str|None]     = mapped_column(String(100))
    country:             Mapped[str]          = mapped_column(String(2), default="GB")
    payment_terms_days:  Mapped[int]          = mapped_column(Integer, default=30)
    bank_account:        Mapped[str|None]     = mapped_column(String(30))
    bank_sort_code:      Mapped[str|None]     = mapped_column(String(10))
    status:              Mapped[VendorStatus] = mapped_column(Enum(VendorStatus), default=VendorStatus.ACTIVE)
    risk_score:          Mapped[float|None]   = mapped_column(Numeric(5, 4))
    is_active:           Mapped[bool]         = mapped_column(Boolean, default=True)

    invoices: Mapped[list["Invoice"]] = relationship("Invoice", back_populates="vendor")


class Invoice(Base, TimestampMixin):
    __tablename__ = "invoices"
    __table_args__ = {"schema": "ap"}

    id:                  Mapped[str]            = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    invoice_number:      Mapped[str]            = mapped_column(String(50), nullable=False)
    vendor_id:           Mapped[str]            = mapped_column(UUID(as_uuid=False), ForeignKey("ap.vendors.id"), nullable=False)
    po_id:               Mapped[str|None]       = mapped_column(UUID(as_uuid=False), ForeignKey("procurement.purchase_orders.id"))
    invoice_date:        Mapped[date]           = mapped_column(Date, nullable=False)
    due_date:            Mapped[date]           = mapped_column(Date, nullable=False)
    received_date:       Mapped[date|None]      = mapped_column(Date)
    currency:            Mapped[str]            = mapped_column(String(3), default="GBP")
    subtotal:            Mapped[Decimal]        = mapped_column(Numeric(15, 2), nullable=False)
    tax_amount:          Mapped[Decimal]        = mapped_column(Numeric(15, 2), default=0)
    total_amount:        Mapped[Decimal]        = mapped_column(Numeric(15, 2), nullable=False)
    status:              Mapped[InvoiceStatus]  = mapped_column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    description:         Mapped[str|None]       = mapped_column(Text)
    file_path:           Mapped[str|None]       = mapped_column(String(500))
    category:            Mapped[str|None]       = mapped_column(String(50))
    is_duplicate:        Mapped[bool]           = mapped_column(Boolean, default=False)
    duplicate_of_id:     Mapped[str|None]       = mapped_column(UUID(as_uuid=False), ForeignKey("ap.invoices.id"))
    ocr_extracted:       Mapped[dict|None]      = mapped_column(JSONB)
    suggested_gl_account:Mapped[str|None]       = mapped_column(String(20))

    vendor:  Mapped[Vendor]              = relationship("Vendor", back_populates="invoices")
    lines:   Mapped[list["InvoiceLine"]] = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    voucher: Mapped["Voucher|None"]      = relationship("Voucher", back_populates="invoice", uselist=False)


class InvoiceLine(Base, TimestampMixin):
    __tablename__ = "invoice_lines"
    __table_args__ = {"schema": "ap"}

    id:              Mapped[str]     = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    invoice_id:      Mapped[str]     = mapped_column(UUID(as_uuid=False), ForeignKey("ap.invoices.id"), nullable=False)
    line_number:     Mapped[int]     = mapped_column(Integer, nullable=False)
    description:     Mapped[str]     = mapped_column(Text, nullable=False)
    quantity:        Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    unit_price:      Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    amount:          Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_rate:        Mapped[Decimal] = mapped_column(Numeric(5, 4), default=0)
    gl_account_code: Mapped[str|None]= mapped_column(String(20))

    invoice: Mapped[Invoice] = relationship("Invoice", back_populates="lines")


class Voucher(Base, TimestampMixin):
    __tablename__ = "vouchers"
    __table_args__ = {"schema": "ap"}

    id:             Mapped[str]          = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    voucher_number: Mapped[str]          = mapped_column(String(30), unique=True, nullable=False)
    invoice_id:     Mapped[str]          = mapped_column(UUID(as_uuid=False), ForeignKey("ap.invoices.id"), unique=True)
    amount:         Mapped[Decimal]      = mapped_column(Numeric(15, 2), nullable=False)
    currency:       Mapped[str]          = mapped_column(String(3), default="GBP")
    payment_method: Mapped[str]          = mapped_column(String(20), default="bank_transfer")
    scheduled_date: Mapped[date]         = mapped_column(Date, nullable=False)
    paid_date:      Mapped[date|None]    = mapped_column(Date)
    status:         Mapped[str]          = mapped_column(String(20), default="pending")
    approved_by:    Mapped[str|None]     = mapped_column(UUID(as_uuid=False))

    invoice: Mapped[Invoice] = relationship("Invoice", back_populates="voucher")
