from uuid import UUID
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


# ══════════════════════════════════════════════════════════════
# Auth
# ══════════════════════════════════════════════════════════════

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    role: str
    exp: int


# ══════════════════════════════════════════════════════════════
# Merchant
# ══════════════════════════════════════════════════════════════

class MerchantRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    business_name: str = Field(..., min_length=2, max_length=255)
    phone: Optional[str] = None
    business_type: Optional[str] = None
    gstin: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None


class MerchantLogin(BaseModel):
    email: EmailStr
    password: str


class MerchantOut(BaseModel):
    id: UUID
    email: str
    business_name: str
    phone: Optional[str] = None
    business_type: Optional[str] = None
    gstin: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    role: str
    is_active: bool
    is_flagged: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MerchantUpdate(BaseModel):
    business_name: Optional[str] = None
    phone: Optional[str] = None
    business_type: Optional[str] = None
    gstin: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None


# ══════════════════════════════════════════════════════════════
# Supplier
# ══════════════════════════════════════════════════════════════

class SupplierCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    gstin: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    category: Optional[str] = None
    credit_terms: Optional[int] = 0
    avg_delivery_days: Optional[float] = 0
    reliability_score: Optional[float] = Field(0.5, ge=0, le=1)


class SupplierOut(BaseModel):
    id: UUID
    name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    gstin: Optional[str] = None
    city: Optional[str] = None
    category: Optional[str] = None
    credit_terms: Optional[int] = None
    avg_delivery_days: Optional[float] = None
    reliability_score: Optional[float] = None
    is_approved: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    category: Optional[str] = None
    credit_terms: Optional[int] = None
    avg_delivery_days: Optional[float] = None
    reliability_score: Optional[float] = Field(None, ge=0, le=1)


# ══════════════════════════════════════════════════════════════
# Product
# ══════════════════════════════════════════════════════════════

class ProductCreate(BaseModel):
    sku_code: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=255)
    category: Optional[str] = None
    unit: Optional[str] = "piece"
    hsn_code: Optional[str] = None
    description: Optional[str] = None


class ProductOut(BaseModel):
    id: UUID
    sku_code: Optional[str] = None
    name: str
    normalized_name: str
    category: Optional[str] = None
    unit: Optional[str] = None

    class Config:
        from_attributes = True


# ══════════════════════════════════════════════════════════════
# Invoice
# ══════════════════════════════════════════════════════════════

class InvoiceOut(BaseModel):
    id: UUID
    merchant_id: UUID
    supplier_id: Optional[UUID] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    total_amount: Optional[float] = None
    currency: str = "INR"
    file_url: str
    ocr_status: str
    ocr_confidence: Optional[float] = None
    ocr_provider: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InvoiceItemOut(BaseModel):
    id: UUID
    invoice_id: UUID
    product_id: Optional[UUID] = None
    raw_description: str
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    matched_sku: Optional[str] = None
    match_confidence: Optional[float] = None
    
    # Pharma Fields
    batch_number: Optional[str] = None
    expiry_date: Optional[date] = None
    hsn_code: Optional[str] = None
    mrp: Optional[float] = None

    class Config:
        from_attributes = True


class InvoiceItemCorrection(BaseModel):
    item_id: UUID
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    
    # Pharma Fields
    batch_number: Optional[str] = None
    expiry_date: Optional[date] = None
    hsn_code: Optional[str] = None
    mrp: Optional[float] = None


class InvoiceVerification(BaseModel):
    corrections: List[InvoiceItemCorrection]


# ══════════════════════════════════════════════════════════════
# Score
# ══════════════════════════════════════════════════════════════

class ScoreOut(BaseModel):
    id: UUID
    merchant_id: UUID
    supplier_id: UUID
    product_id: Optional[UUID] = None
    credit_score: float
    price_score: float
    reliability_score: float
    switching_friction: float
    delivery_speed: float
    total_score: float
    weights_snapshot: Optional[dict] = None
    calculated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ══════════════════════════════════════════════════════════════
# Recommendation
# ══════════════════════════════════════════════════════════════

class RecommendationOut(BaseModel):
    id: UUID
    merchant_id: UUID
    invoice_id: Optional[UUID] = None
    product_id: Optional[UUID] = None
    recommended_supplier_id: Optional[UUID] = None
    current_supplier_id: Optional[UUID] = None
    product_name: Optional[str] = None
    recommended_supplier_name: Optional[str] = None
    current_supplier_name: Optional[str] = None
    savings_estimate: Optional[float] = None
    reason: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RecommendationUpdate(BaseModel):
    status: str = Field(..., pattern="^(accepted|rejected)$")


# ══════════════════════════════════════════════════════════════
# Admin
# ══════════════════════════════════════════════════════════════

class WeightsUpdate(BaseModel):
    credit_score: float = Field(..., ge=0, le=1)
    price_score: float = Field(..., ge=0, le=1)
    reliability_score: float = Field(..., ge=0, le=1)
    switching_friction: float = Field(..., ge=0, le=1)
    delivery_speed: float = Field(..., ge=0, le=1)


class AdminAnalytics(BaseModel):
    total_merchants: int
    total_suppliers: int
    total_invoices: int
    invoices_processed: int
    invoices_pending: int
    total_recommendations: int
    flagged_merchants: int
    realized_savings: float = 0.0


class ActivityLogOut(BaseModel):
    id: UUID
    actor_id: Optional[UUID] = None
    actor_role: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[UUID] = None
    details: Optional[dict] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ══════════════════════════════════════════════════════════════
# Common
# ══════════════════════════════════════════════════════════════

class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    per_page: int
    pages: int


class MessageResponse(BaseModel):
    message: str
