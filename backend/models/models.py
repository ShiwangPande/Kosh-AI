
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Float, Text, Date, Numeric, DateTime, Integer, Time,
    ForeignKey, Index, CheckConstraint, UniqueConstraint, JSON, func, select, cast
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
from backend.database import Base


# ── Mixins ──────────────────────────────────────────────────

class TimestampMixin:
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ── Merchant ────────────────────────────────────────────────

class Merchant(TimestampMixin, Base):
    __tablename__ = "merchants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20))
    password_hash = Column(String(255), nullable=False)
    business_name = Column(String(255), nullable=False)
    business_type = Column(String(100))
    gstin = Column(String(20))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    pincode = Column(String(10))
    role = Column(String(20), nullable=False, default="merchant")
    
    # Notification Preferences
    preferred_channel = Column(String(20), default="WHATSAPP") # WHATSAPP, EMAIL, SMS
    quiet_hours_start = Column(Time, nullable=True) # e.g. 22:00
    quiet_hours_end = Column(Time, nullable=True)   # e.g. 08:00
    
    is_active = Column(Boolean, nullable=False, default=True)
    is_flagged = Column(Boolean, nullable=False, default=False)
    flag_reason = Column(Text)
    reset_token = Column(String(255), nullable=True)
    reset_token_expiry = Column(DateTime(timezone=True), nullable=True)

    invoices = relationship("Invoice", back_populates="merchant", cascade="all, delete-orphan")
    scores = relationship("Score", back_populates="merchant", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="merchant", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="merchant", cascade="all, delete-orphan")


# ── Supplier ────────────────────────────────────────────────

class Supplier(TimestampMixin, Base):
    __tablename__ = "suppliers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    contact_person = Column(String(255))
    email = Column(String(255))
    phone = Column(String(20))
    gstin = Column(String(20))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    pincode = Column(String(10))
    category = Column(String(100), index=True)
    credit_terms = Column(Float, default=0)
    avg_delivery_days = Column(Float, default=0)
    
    # Intelligence Scores (Phase 8)
    reliability_score = Column(Float, default=0.5)
    price_consistency_score = Column(Float, default=0.5)
    delivery_speed_score = Column(Float, default=0.5)
    last_score_update = Column(DateTime(timezone=True))
    
    is_approved = Column(Boolean, nullable=False, default=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("merchants.id"))

    invoice_items = relationship("InvoiceItem", secondary="invoices",
                                 viewonly=True)


# ── Product ─────────────────────────────────────────────────

class Product(TimestampMixin, Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku_code = Column(String(100), unique=True, index=True)
    name = Column(String(255), nullable=False)
    normalized_name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), index=True)
    unit = Column(String(50), default="piece")
    hsn_code = Column(String(20))
    description = Column(Text)


# ── Invoice ─────────────────────────────────────────────────

class Invoice(TimestampMixin, Base):
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="SET NULL"),
                         index=True)
    invoice_number = Column(String(100))
    invoice_date = Column(Date)
    total_amount = Column(Numeric(12, 2))
    currency = Column(String(3), default="INR")
    file_url = Column(Text, nullable=False)
    file_key = Column(String(500), nullable=False)
    ocr_status = Column(
        String(20),
        CheckConstraint("ocr_status IN ('pending', 'processing', 'completed', 'failed', 'needs_review', 'verified')"),
        nullable=False,
        default="pending"
    )
    ocr_task_id = Column(String(100))
    ocr_raw_text = Column(Text)
    ocr_confidence = Column(Float)
    ocr_provider = Column(String(20))
    processed_at = Column(DateTime(timezone=True))

    merchant = relationship("Merchant", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")

    # Composite index for common query: list invoices by merchant + status (P4)
    __table_args__ = (
        Index("ix_invoices_merchant_status", "merchant_id", "ocr_status"),
    )


# ── InvoiceItem ─────────────────────────────────────────────

class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"),
                        index=True)
    raw_description = Column(Text, nullable=False)
    quantity = Column(Numeric(10, 3))
    unit_price = Column(Numeric(12, 2))
    total_price = Column(Numeric(12, 2))
    matched_sku = Column(String(100))
    match_confidence = Column(Float)
    
    # Pharma / Vertical Fields (Phase 7)
    batch_number = Column(String(50))
    expiry_date = Column(Date) # Parsed expiry
    hsn_code = Column(String(20))
    mrp = Column(Numeric(12, 2)) # Maximum Retail Price
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    invoice = relationship("Invoice", back_populates="items")
    product = relationship("Product")

    # Composite index for comparison engine lookups (P4)
    __table_args__ = (
        Index("ix_invoice_items_product_invoice", "product_id", "invoice_id"),
    )


# ── Orders (Phase 9) ────────────────────────────────────────

class Order(TimestampMixin, Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="SET NULL"), index=True)
    
    po_number = Column(String(50), index=True) # e.g. PO-2023-001
    status = Column(String(20), default="draft") # draft, sent, partial, completed, cancelled
    total_amount = Column(Numeric(12, 2), default=0)
    expected_delivery_date = Column(Date)
    
    merchant = relationship("Merchant", back_populates="orders")
    supplier = relationship("Supplier")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"))
    
    description = Column(String(255)) # Backup if product deleted
    quantity = Column(Float, nullable=False)
    unit_price = Column(Numeric(12, 2))
    total_price = Column(Numeric(12, 2))
    
    received_quantity = Column(Float, default=0) # For tracking fulfillment

    order = relationship("Order", back_populates="items")
    product = relationship("Product")


# ── Score ───────────────────────────────────────────────────

class Score(Base):
    __tablename__ = "scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"))
    credit_score = Column(Float, nullable=False, default=0)
    price_score = Column(Float, nullable=False, default=0)
    reliability_score = Column(Float, nullable=False, default=0)
    switching_friction = Column(Float, nullable=False, default=0)
    delivery_speed = Column(Float, nullable=False, default=0)
    total_score = Column(Float, nullable=False, default=0)
    weights_snapshot = Column(JSONB)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    merchant = relationship("Merchant", back_populates="scores")
    supplier = relationship("Supplier")
    product = relationship("Product")

    __table_args__ = (
        UniqueConstraint("merchant_id", "supplier_id", "product_id"),
    )


# ── Recommendation ──────────────────────────────────────────

class Recommendation(TimestampMixin, Base):
    __tablename__ = "recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="SET NULL"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"))
    recommended_supplier_id = Column(UUID(as_uuid=True),
                                     ForeignKey("suppliers.id", ondelete="SET NULL"))
    current_supplier_id = Column(UUID(as_uuid=True),
                                 ForeignKey("suppliers.id", ondelete="SET NULL"))
    score_id = Column(UUID(as_uuid=True), ForeignKey("scores.id", ondelete="SET NULL"))
    savings_estimate = Column(Numeric(12, 2))
    reason = Column(Text)
    status = Column(String(20), nullable=False, default="pending")

    merchant = relationship("Merchant", back_populates="recommendations")
    invoice = relationship("Invoice")
    product = relationship("Product")
    recommended_supplier = relationship("Supplier", foreign_keys=[recommended_supplier_id])
    current_supplier = relationship("Supplier", foreign_keys=[current_supplier_id])
    score = relationship("Score")


# ── ActivityLog ─────────────────────────────────────────────

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="SET NULL"),
                      index=True)
    actor_role = Column(String(20))
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), index=True)
    resource_id = Column(UUID(as_uuid=True))
    details = Column(JSONB)
    ip_address = Column(INET)
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# ── AdminSetting ────────────────────────────────────────────

class AdminSetting(Base):
    __tablename__ = "admin_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(JSONB, nullable=False)
    description = Column(Text)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("merchants.id"))
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ── WhatsAppMessage ─────────────────────────────────────────

class WhatsAppMessage(Base):
    __tablename__ = "whatsapp_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="SET NULL"),
                         index=True)
    direction = Column(String(10), nullable=False)
    phone_number = Column(String(20), nullable=False, index=True)
    message_type = Column(String(20), default="text")
    content = Column(Text)
    media_url = Column(Text)
    status = Column(String(20), default="received")
    external_id = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# ── Learning System Models ──────────────────────────────────

class RecommendationFeedback(Base):
    """Stores merchant interaction with recommendations."""
    __tablename__ = "recommendation_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    recommendation_id = Column(UUID(as_uuid=True), ForeignKey("recommendations.id"),
                               index=True)
    accepted = Column(Boolean, nullable=False)
    supplier_selected = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"))
    time_to_decision = Column(Float)  # Seconds
    price_difference = Column(Float)  # Savings or extra cost
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class MerchantPreference(TimestampMixin, Base):
    """Learned preference weights for each merchant."""
    __tablename__ = "merchant_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"),
                         nullable=False, unique=True, index=True)
    
    # Weights (Must sum to 1.0 approx)
    credit_weight = Column(Float, default=0.30)
    price_weight = Column(Float, default=0.25)
    reliability_weight = Column(Float, default=0.20)
    switching_weight = Column(Float, default=0.15)
    speed_weight = Column(Float, default=0.10)
    
    version = Column(Integer, default=1)
    last_trained_at = Column(DateTime(timezone=True))


class ModelVersion(Base):
    """Track global model performance and training history."""
    __tablename__ = "model_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    active_at = Column(DateTime(timezone=True), server_default=func.now())
    metrics = Column(JSONB)  # Accuracy, Agreement Score, etc.
    parameters_snapshot = Column(JSONB)  # Global defaults if any
    is_rollback = Column(Boolean, default=False)


class ConfidenceMetric(Base):
    """Calibration tracking: Predicted vs Actual savings."""
    __tablename__ = "confidence_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), index=True)
    predicted_savings = Column(Float)
    actual_savings = Column(Float)
    error_margin = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ── Network Intelligence Models ─────────────────────────────

class AggregatedPrice(Base):
    """Precomputed market price stats by product/city/time."""
    __tablename__ = "aggregated_prices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)
    city = Column(String(100), index=True)  # Generalized location
    time_window = Column(DateTime(timezone=True), index=True) # Start of window
    
    currency = Column(String(3), default="INR")
    median_price = Column(Float)
    p25_price = Column(Float)
    p75_price = Column(Float)
    volatility = Column(Float)
    data_points = Column(Integer) # Number of transactions aggregated
    merchant_count = Column(Integer) # For privacy check (must be >= 5)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SupplierBenchmark(Base):
    """Network-wide supplier scoring and ranking."""
    __tablename__ = "supplier_benchmarks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False, index=True)
    city = Column(String(100), index=True)
    
    price_competitiveness = Column(Float) # 0-100
    delivery_reliability = Column(Float)
    fulfillment_accuracy = Column(Float)
    merchant_retention = Column(Float)
    
    network_rank = Column(Integer)
    total_suppliers_in_region = Column(Integer)
    
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class MarketTrend(Base):
    """Detected market-wide trends."""
    __tablename__ = "market_trends"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), index=True)
    city = Column(String(100), index=True)
    trend_type = Column(String(50)) # PRICE_SPIKE, SUPPLY_SHORTAGE, SEASONAL
    
    direction = Column(String(10)) # UP, DOWN
    magnitude = Column(Float) # Std deviations
    confidence = Column(Float)
    
    detected_at = Column(DateTime(timezone=True), server_default=func.now())


class RiskAlert(Base):
    """Supplier or market risk alerts."""
    __tablename__ = "risk_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_type = Column(String(50)) # SUPPLIER_DISAPPEARED, PRICE_COLLUSION
    severity = Column(String(20)) # HIGH, MEDIUM, LOW
    target_id = Column(UUID(as_uuid=True)) # Supplier ID or Product ID
    description = Column(Text)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ── Predictive Intelligence Models ──────────────────────────

class PricePrediction(Base):
    """Forecasted product prices."""
    __tablename__ = "price_predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), index=True)
    city = Column(String(100), index=True)
    target_date = Column(Date, index=True)
    
    predicted_price = Column(Float)
    confidence_score = Column(Float) # 0.0 - 1.0
    trend_direction = Column(String(20)) # UP, DOWN, STABLE
    
    explanation = Column(JSONB) # Contributing factors
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DemandPrediction(Base):
    """Forecasted demand for merchant."""
    __tablename__ = "demand_predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    target_date = Column(Date)
    
    expected_quantity = Column(Float)
    confidence_score = Column(Float)
    
    explanation = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RestockPrediction(Base):
    """Optimal restock recommendations."""
    __tablename__ = "restock_predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    
    recommended_date = Column(Date)
    recommended_quantity = Column(Float)
    urgency_score = Column(Float) # 0-100
    
    explanation = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SupplierRiskPrediction(Base):
    """Predicted supplier risks."""
    __tablename__ = "supplier_risk_predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), index=True)
    risk_type = Column(String(50)) # LATE_DELIVERY, STOCKOUT
    
    probability = Column(Float) # 0.0 - 1.0
    risk_score = Column(Float) # 0-100
    
    explanation = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ── Autonomous Optimization Models ──────────────────────────

class SystemMetric(Base):
    """System-wide KPIs tracked over time."""
    __tablename__ = "system_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_name = Column(String(50), index=True) # acceptance_rate, savings_avg, latency_ms
    value = Column(Float)
    window_start = Column(DateTime(timezone=True))
    window_end = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ModelRegistry(Base):
    """Track ML models and recommendation versions."""
    __tablename__ = "model_registry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String(100))
    version = Column(String(20))
    status = Column(String(20)) # ACTIVE, CANDIDATE, ARCHIVED
    config = Column(JSONB) # Hyperparameters or weights
    
    performance_score = Column(Float)
    is_baseline = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Experiment(Base):
    """A/B Tests."""
    __tablename__ = "experiments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100))
    status = Column(String(20)) # RUNNING, COMPLETED, FAILED
    
    control_model_id = Column(UUID(as_uuid=True), ForeignKey("model_registry.id"))
    candidate_model_id = Column(UUID(as_uuid=True), ForeignKey("model_registry.id"))
    
    traffic_split = Column(Float) # 0.0 - 1.0 (Exposure)
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    
    results = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class WeightHistory(Base):
    """History of weight tuning adjustments."""
    __tablename__ = "weight_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), nullable=True) # Null for global defaults
    previous_weights = Column(JSONB)
    new_weights = Column(JSONB)
    
    reason = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class OptimizationLog(Base):
    """Audit log of autonomous actions."""
    __tablename__ = "optimization_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action_type = Column(String(50)) # WEIGHT_TUNE, MODEL_SWITCH, ROLLBACK
    status = Column(String(20))
    details = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# ── Market Intelligence ─────────────────────────────────────

class MarketIndex(TimestampMixin, Base):
    """Live aggregation of pricing data from all verified invoices."""
    __tablename__ = "market_index"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    normalized_product_name = Column(String(255), unique=True, index=True, nullable=False)
    product_category = Column(String(100), index=True)
    
    # Pricing Stats
    avg_price = Column(Numeric(10, 2), nullable=False)
    min_price = Column(Numeric(10, 2), nullable=False)
    max_price = Column(Numeric(10, 2), nullable=False)
    
    # Metadata
    sample_size = Column(Integer, default=0, nullable=False)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    region = Column(String(100), index=True) # e.g., "Mumbai", "Maharashtra"


# ── Immutable Ledger ────────────────────────────────────────

class LedgerAccount(Base):
    """Source of truth for all balances.
    
    Stores the current balance for any entity (Merchant, Supplier, System)
    in a specific currency and account type (Wallet, Credit, Payable, Receivable).
    
    Balance is denormalized for read performance but MUST match sum of entries.
    """
    __tablename__ = "ledger_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_type = Column(String(20), nullable=False) # MERCHANT, SUPPLIER, SYSTEM
    owner_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    account_type = Column(String(20), nullable=False) # WALLET, CREDIT, PAYABLE, RECEIVABLE
    currency = Column(String(3), default="INR", nullable=False)
    
    # Balance must be updated atomically with transactions
    balance = Column(Numeric(20, 4), default=0, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_frozen = Column(Boolean, default=False)
    version = Column(Integer, default=1) # Optimistic locking
    
    # Ensure one account per type/currency per owner
    __table_args__ = (
        UniqueConstraint('owner_id', 'owner_type', 'account_type', 'currency', name='uq_ledger_account_owner_currency'),
    )

class LedgerTransaction(Base):
    """The atomic event wrapper.
    
    Represents a single business event (e.g., "Payment for Order #123")
    that results in multiple ledger entries.
    """
    __tablename__ = "ledger_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    idempotency_key = Column(String(100), unique=True, index=True, nullable=False)
    
    reference_type = Column(String(50)) # ORDER_PAYMENT, LOAN_DISBURSAL, FEE
    reference_id = Column(UUID(as_uuid=True), index=True)
    
    description = Column(Text)
    posted_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20), default="posted") # posted, voided

    # Metadata for tracing
    created_by = Column(UUID(as_uuid=True)) # User ID or System ID
    
    # Hash for chain integrity (Phase 2)
    entry_hash = Column(String(64))

class LedgerEntry(Base):
    """The immutable lines. Must sum to zero per Transaction ID.
    
    Represents a single debit or credit to a specific account.
    """
    __tablename__ = "ledger_entries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("ledger_transactions.id"), nullable=False, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("ledger_accounts.id"), nullable=False, index=True)
    
    direction = Column(String(10), nullable=False) # DEBIT, CREDIT
    amount = Column(Numeric(20, 4), nullable=False)
    
    # Snapshot of account balance AFTER this entry
    balance_after = Column(Numeric(20, 4), nullable=False) 
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    account = relationship("LedgerAccount")
    transaction = relationship("LedgerTransaction", backref="entries")
    
    __table_args__ = (
        CheckConstraint("amount > 0", name="check_ledger_entry_positive_amount"),
        CheckConstraint("direction IN ('DEBIT', 'CREDIT')", name="check_ledger_entry_direction"),
    )


# ── Habit & Trigger Engine (Phase 10) ───────────────────────

class TriggerEvent(Base):
    """
    Persistent opportunity/alert for a merchant.
    The core atom of the Habit Layer.
    """
    __tablename__ = "trigger_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), nullable=False, index=True)
    
    event_type = Column(String(50), nullable=False) # PRICE_DROP, RISK_ALERT, PAYMENT_DUE
    priority = Column(Integer, nullable=False) # 1=Critical, 2=High, 3=Medium, 4=Low
    
    payload = Column(JSONB, nullable=False) # Dynamic data for the UI/WhatsApp
    status = Column(String(20), default="PENDING", index=True) # PENDING, SENT, DISMISSED, ACTED
    
    dedupe_key = Column(String(255), index=True) # hash(merchant_id + type + target_id)
    
    expires_at = Column(DateTime(timezone=True), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Retry Logic
    retry_count = Column(Integer, default=0)
    next_retry_at = Column(DateTime(timezone=True))
    
    # Index for fast retrieval of active triggers
    __table_args__ = (
        Index("ix_triggers_merchant_status_priority", "merchant_id", "status", "priority"),
        Index("ix_triggers_pending_queue", "status", "next_retry_at", "priority", "created_at"),
    )


class NotificationTemplate(Base):
    __tablename__ = "notification_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(50), unique=True, nullable=False) # PRICE_DROP
    channel = Column(String(20), default="WHATSAPP")
    template_body = Column(Text, nullable=False) # "Sugar dropped..."
    is_active = Column(Boolean, default=True)


class NotificationLog(Base):
    __tablename__ = "notification_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trigger_id = Column(UUID(as_uuid=True), ForeignKey("trigger_events.id"), index=True)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), index=True)
    
    channel = Column(String(20))
    status = Column(String(20)) # SENT, FAILED, DELIVERED
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    channel = Column(String(20))
    status = Column(String(20)) # SENT, FAILED, DELIVERED
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    response = Column(String(50)) # YES/NO


class UserAction(Base):
    """
    Captures user intent (YES/NO) in response to a Trigger.
    """
    __tablename__ = "user_actions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), index=True)
    trigger_id = Column(UUID(as_uuid=True), ForeignKey("trigger_events.id"), index=True)
    
    action_type = Column(String(50), nullable=False) # ACCEPT, DISMISS
    raw_response = Column(Text)
    
    status = Column(String(20), default="RECEIVED") # RECEIVED, VALIDATED, EXECUTED, FAILED
    
    executed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Idempotency Constraint: One action type per trigger per merchant (e.g. can't Accept twice)
    # But maybe can Accept then Cancel? For 'One-Tap' simplest is unique constraint.
    __table_args__ = (
        UniqueConstraint('merchant_id', 'trigger_id', 'action_type', name='uq_action_idempotency'),
    )


# ── Data Moat & Proprietary Signals (Phase 11) ──────────────

class NegotiationSignal(Base):
    """
    Captures why a user said NO (or YES).
    Proprietary dataset for training future Negotiation Bots.
    """
    __tablename__ = "negotiation_signals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), index=True)
    trigger_id = Column(UUID(as_uuid=True), ForeignKey("trigger_events.id"), index=True)
    
    message_text = Column(Text, nullable=False) # "Too expensive, give me 36"
    intent_detected = Column(String(50)) # COUNTER_OFFER, REJECTION_PRICE
    
    # Derived Features (Boolean Flags for quick filtering)
    price_objection = Column(Boolean, default=False)
    credit_request = Column(Boolean, default=False)
    trust_issue = Column(Boolean, default=False)
    delivery_issue = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class IntentSignal(Base):
    """
    Captures demand *before* a transaction happens.
    Source: Search bar, Voice notes, WhatsApp text.
    """
    __tablename__ = "intent_signals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), index=True)
    
    text = Column(Text, nullable=False) # "Need 50kg Sugar tomorrow"
    normalized_product = Column(String(255)) # SUGAR-50KG
    urgency_level = Column(String(20)) # HIGH, MEDIUM, LOW
    expected_qty = Column(Float)
    
    captured_from = Column(String(20)) # SEARCH, MESSAGE, VOICE
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DecisionContext(Base):
    """
    Snapshot of the 'State of the World' when a user made a decision.
    Essential for Counterfactual Training/RL.
    """
    __tablename__ = "decision_contexts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), index=True)
    trigger_id = Column(UUID(as_uuid=True), ForeignKey("trigger_events.id"), index=True)
    user_action_id = Column(UUID(as_uuid=True), ForeignKey("user_actions.id"), unique=True)
    
    # Context Features
    price_at_time = Column(Numeric(10, 2))
    supplier_score = Column(Float)
    risk_score = Column(Float)
    credit_available = Column(Numeric(12, 2))
    time_of_day = Column(Time) # Local time
    day_of_week = Column(Integer) # 0=Mon, 6=Sun
    response_time_ms = Column(Integer) # Time from Trigger Sent -> Action
    
    decision = Column(String(20)) # ACCEPT / REJECT
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RiskDecisionLog(Base):
    """
    Full trace of Risk Engine inputs & outputs.
    Allows offline model retraining.
    """
    __tablename__ = "risk_decision_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), index=True)
    transaction_id = Column(String(100), index=True) # Optional correlation ID
    
    risk_score = Column(Float)
    decision = Column(String(20))
    
    # The 'Black Box' inputs
    features_json = Column(JSONB) # {velocity: 5, amount: 5000, history_len: 10}
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SupplierPerformanceSignal(Base):
    """
    Granular, per-delivery feedback.
    """
    __tablename__ = "supplier_performance_signals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), index=True)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), index=True)
    
    delivery_time_days = Column(Float) 
    condition_rating = Column(Integer) # 1-5
    accuracy_rating = Column(Integer) # 1-5
    comment = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class EventLog(Base):
    """
    Immutable, append-only system event stream.
    Replay Source.
    """
    __tablename__ = "event_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(50), index=True) # TRIGGER_CREATED, ACTION_RECEIVED
    entity_id = Column(UUID(as_uuid=True), index=True)
    payload = Column(JSONB)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ── User Onboarding State ──────────────────────────────────

class UserOnboardingState(TimestampMixin, Base):
    __tablename__ = "user_onboarding_states"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    step = Column(String(50), default="WELCOME") # WELCOME, UPLOAD_INVOICE, INSIGHT_REVEAL, FIRST_RECOMMENDATION, ACTION_DEMO, COMPLETED
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True))
    skipped = Column(Boolean, default=False)
    onboarding_metadata = Column(JSONB, default={})

    merchant = relationship("Merchant", backref="onboarding_state")


# ── Documentation System ───────────────────────────────────

class DocArticle(TimestampMixin, Base):
    __tablename__ = "doc_articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    summary = Column(Text)
    content = Column(Text) # Markdown content
    category = Column(String(100))
    order_index = Column(Integer, default=0)
    is_published = Column(Boolean, default=True)

    __table_args__ = (
        Index('ix_doc_articles_category_order', 'category', 'order_index'),
    )



