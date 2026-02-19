-- ============================================================
-- Kosh-AI Database Schema
-- Procurement Intelligence Engine for Merchants
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- MERCHANTS
-- ============================================================
CREATE TABLE merchants (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    phone           VARCHAR(20),
    password_hash   VARCHAR(255) NOT NULL,
    business_name   VARCHAR(255) NOT NULL,
    business_type   VARCHAR(100),
    gstin           VARCHAR(20),
    address         TEXT,
    city            VARCHAR(100),
    state           VARCHAR(100),
    pincode         VARCHAR(10),
    role            VARCHAR(20) NOT NULL DEFAULT 'merchant'
                    CHECK (role IN ('merchant', 'admin', 'analyst')),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    is_flagged      BOOLEAN NOT NULL DEFAULT FALSE,
    flag_reason     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_merchants_email ON merchants(email);
CREATE INDEX idx_merchants_role ON merchants(role);
CREATE INDEX idx_merchants_is_active ON merchants(is_active);
CREATE INDEX idx_merchants_city ON merchants(city);

-- ============================================================
-- SUPPLIERS
-- ============================================================
CREATE TABLE suppliers (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(255) NOT NULL,
    contact_person  VARCHAR(255),
    email           VARCHAR(255),
    phone           VARCHAR(20),
    gstin           VARCHAR(20),
    address         TEXT,
    city            VARCHAR(100),
    state           VARCHAR(100),
    pincode         VARCHAR(10),
    category        VARCHAR(100),
    credit_terms    INTEGER DEFAULT 0,              -- days
    avg_delivery_days FLOAT DEFAULT 0,
    reliability_score FLOAT DEFAULT 0.5             -- 0.0 - 1.0
                    CHECK (reliability_score >= 0 AND reliability_score <= 1),
    is_approved     BOOLEAN NOT NULL DEFAULT FALSE,
    approved_by     UUID REFERENCES merchants(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_suppliers_name ON suppliers(name);
CREATE INDEX idx_suppliers_category ON suppliers(category);
CREATE INDEX idx_suppliers_city ON suppliers(city);
CREATE INDEX idx_suppliers_is_approved ON suppliers(is_approved);

-- ============================================================
-- PRODUCTS (normalized SKU catalog)
-- ============================================================
CREATE TABLE products (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sku_code        VARCHAR(100) UNIQUE,
    name            VARCHAR(255) NOT NULL,
    normalized_name VARCHAR(255) NOT NULL,
    category        VARCHAR(100),
    unit            VARCHAR(50) DEFAULT 'piece',
    hsn_code        VARCHAR(20),
    description     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_products_sku_code ON products(sku_code);
CREATE INDEX idx_products_normalized_name ON products(normalized_name);
CREATE INDEX idx_products_category ON products(category);

-- ============================================================
-- INVOICES
-- ============================================================
CREATE TABLE invoices (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_id     UUID NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    supplier_id     UUID REFERENCES suppliers(id) ON DELETE SET NULL,
    invoice_number  VARCHAR(100),
    invoice_date    DATE,
    total_amount    NUMERIC(12,2),
    currency        VARCHAR(3) DEFAULT 'INR',
    file_url        TEXT NOT NULL,
    file_key        VARCHAR(500) NOT NULL,          -- S3 object key
    ocr_status      VARCHAR(20) NOT NULL DEFAULT 'pending'
                    CHECK (ocr_status IN ('pending', 'processing', 'completed', 'failed')),
    ocr_raw_text    TEXT,
    ocr_confidence  FLOAT,
    ocr_provider    VARCHAR(20),                    -- 'google_vision' | 'tesseract'
    processed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_invoices_merchant_id ON invoices(merchant_id);
CREATE INDEX idx_invoices_supplier_id ON invoices(supplier_id);
CREATE INDEX idx_invoices_ocr_status ON invoices(ocr_status);
CREATE INDEX idx_invoices_created_at ON invoices(created_at);

-- ============================================================
-- INVOICE ITEMS
-- ============================================================
CREATE TABLE invoice_items (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id      UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    product_id      UUID REFERENCES products(id) ON DELETE SET NULL,
    raw_description TEXT NOT NULL,
    quantity        NUMERIC(10,3),
    unit_price      NUMERIC(12,2),
    total_price     NUMERIC(12,2),
    matched_sku     VARCHAR(100),
    match_confidence FLOAT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_invoice_items_invoice_id ON invoice_items(invoice_id);
CREATE INDEX idx_invoice_items_product_id ON invoice_items(product_id);

-- ============================================================
-- SCORES (supplier value scores per merchant)
-- ============================================================
CREATE TABLE scores (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_id     UUID NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    supplier_id     UUID NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    product_id      UUID REFERENCES products(id) ON DELETE SET NULL,
    credit_score    FLOAT NOT NULL DEFAULT 0
                    CHECK (credit_score >= 0 AND credit_score <= 1),
    price_score     FLOAT NOT NULL DEFAULT 0
                    CHECK (price_score >= 0 AND price_score <= 1),
    reliability_score FLOAT NOT NULL DEFAULT 0
                    CHECK (reliability_score >= 0 AND reliability_score <= 1),
    switching_friction FLOAT NOT NULL DEFAULT 0
                    CHECK (switching_friction >= 0 AND switching_friction <= 1),
    delivery_speed  FLOAT NOT NULL DEFAULT 0
                    CHECK (delivery_speed >= 0 AND delivery_speed <= 1),
    total_score     FLOAT NOT NULL DEFAULT 0,
    weights_snapshot JSONB,                         -- weights used at calculation time
    calculated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(merchant_id, supplier_id, product_id)
);

CREATE INDEX idx_scores_merchant_id ON scores(merchant_id);
CREATE INDEX idx_scores_supplier_id ON scores(supplier_id);
CREATE INDEX idx_scores_total_score ON scores(total_score DESC);

-- ============================================================
-- RECOMMENDATIONS
-- ============================================================
CREATE TABLE recommendations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_id     UUID NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    invoice_id      UUID REFERENCES invoices(id) ON DELETE SET NULL,
    product_id      UUID REFERENCES products(id) ON DELETE SET NULL,
    recommended_supplier_id UUID REFERENCES suppliers(id) ON DELETE SET NULL,
    current_supplier_id     UUID REFERENCES suppliers(id) ON DELETE SET NULL,
    score_id        UUID REFERENCES scores(id) ON DELETE SET NULL,
    savings_estimate NUMERIC(12,2),
    reason          TEXT,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'accepted', 'rejected', 'expired')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_recommendations_merchant_id ON recommendations(merchant_id);
CREATE INDEX idx_recommendations_status ON recommendations(status);

-- ============================================================
-- ACTIVITY LOGS (Audit)
-- ============================================================
CREATE TABLE activity_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor_id        UUID REFERENCES merchants(id) ON DELETE SET NULL,
    actor_role      VARCHAR(20),
    action          VARCHAR(100) NOT NULL,
    resource_type   VARCHAR(50),
    resource_id     UUID,
    details         JSONB,
    ip_address      INET,
    user_agent      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_activity_logs_actor_id ON activity_logs(actor_id);
CREATE INDEX idx_activity_logs_action ON activity_logs(action);
CREATE INDEX idx_activity_logs_resource_type ON activity_logs(resource_type);
CREATE INDEX idx_activity_logs_created_at ON activity_logs(created_at DESC);

-- ============================================================
-- ADMIN SETTINGS (configurable weights, feature flags)
-- ============================================================
CREATE TABLE admin_settings (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key             VARCHAR(100) UNIQUE NOT NULL,
    value           JSONB NOT NULL,
    description     TEXT,
    updated_by      UUID REFERENCES merchants(id),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed default value score weights
INSERT INTO admin_settings (key, value, description) VALUES
(
    'value_score_weights',
    '{"credit_score": 0.30, "price_score": 0.25, "reliability_score": 0.20, "switching_friction": 0.15, "delivery_speed": 0.10}',
    'Weights for Value Score calculation. Must sum to 1.0.'
);

-- ============================================================
-- WHATSAPP WEBHOOK LOG
-- ============================================================
CREATE TABLE whatsapp_messages (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_id     UUID REFERENCES merchants(id) ON DELETE SET NULL,
    direction       VARCHAR(10) NOT NULL CHECK (direction IN ('inbound', 'outbound')),
    phone_number    VARCHAR(20) NOT NULL,
    message_type    VARCHAR(20) DEFAULT 'text',
    content         TEXT,
    media_url       TEXT,
    status          VARCHAR(20) DEFAULT 'received',
    external_id     VARCHAR(255),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_whatsapp_messages_merchant_id ON whatsapp_messages(merchant_id);
CREATE INDEX idx_whatsapp_messages_phone ON whatsapp_messages(phone_number);

-- ============================================================
-- Updated-at trigger function
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to all tables with updated_at
CREATE TRIGGER update_merchants_updated_at BEFORE UPDATE ON merchants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_suppliers_updated_at BEFORE UPDATE ON suppliers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_invoices_updated_at BEFORE UPDATE ON invoices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_recommendations_updated_at BEFORE UPDATE ON recommendations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
