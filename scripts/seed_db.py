"""Seed database with sample data for development."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.config import get_settings
from backend.models.models import (
    Merchant, Supplier, Product, AdminSetting,
)
from backend.utils.auth import hash_password

settings = get_settings()
engine = create_engine(settings.DATABASE_URL_SYNC)
Session = sessionmaker(bind=engine)


def seed():
    session = Session()

    # ── Admin User ──────────────────────────────────────────
    admin = Merchant(
        email="admin@kosh.ai",
        password_hash=hash_password("Admin@123"),
        business_name="Kosh Admin",
        phone="+919876543210",
        role="admin",
        city="Mumbai",
        state="Maharashtra",
    )
    session.add(admin)

    # ── Merchants ───────────────────────────────────────────
    merchants = [
        # Simple test credentials for development
        Merchant(
            email="test@test.com",
            password_hash=hash_password("Test@123"),
            business_name="Test Merchant",
            phone="+919999999999",
            role="merchant",
            city="Mumbai",
            state="Maharashtra",
        ),
        Merchant(
            email="merchant1@example.com",
            password_hash=hash_password("Pass@123"),
            business_name="Sharma General Store",
            phone="+919876543211",
            business_type="Retail",
            city="Delhi",
            state="Delhi",
            gstin="07AAACH7409R1ZZ",
        ),
        Merchant(
            email="merchant2@example.com",
            password_hash=hash_password("Pass@123"),
            business_name="Patel Electronics",
            phone="+919876543212",
            business_type="Electronics",
            city="Ahmedabad",
            state="Gujarat",
            gstin="24AALCT1234F1ZH",
        ),
    ]
    session.add_all(merchants)

    # ── Suppliers ───────────────────────────────────────────
    suppliers = [
        Supplier(
            name="National Distributors Ltd",
            contact_person="Rajesh Kumar",
            email="rajesh@nationaldist.com",
            phone="+919876543220",
            category="FMCG",
            city="Mumbai",
            state="Maharashtra",
            credit_terms=30,
            avg_delivery_days=3,
            reliability_score=0.85,
            is_approved=True,
        ),
        Supplier(
            name="Delta Electronics Supply",
            contact_person="Priya Menon",
            email="priya@deltaelec.com",
            phone="+919876543221",
            category="Electronics",
            city="Chennai",
            state="Tamil Nadu",
            credit_terms=45,
            avg_delivery_days=5,
            reliability_score=0.78,
            is_approved=True,
        ),
        Supplier(
            name="Green Valley Organics",
            contact_person="Suresh Reddy",
            email="suresh@greenvalley.com",
            phone="+919876543222",
            category="Food",
            city="Hyderabad",
            state="Telangana",
            credit_terms=15,
            avg_delivery_days=2,
            reliability_score=0.92,
            is_approved=True,
        ),
        Supplier(
            name="Metro Wholesale Co",
            contact_person="Anita Singh",
            email="anita@metrowholesale.com",
            phone="+919876543223",
            category="FMCG",
            city="Pune",
            state="Maharashtra",
            credit_terms=60,
            avg_delivery_days=4,
            reliability_score=0.70,
            is_approved=False,
        ),
    ]
    session.add_all(suppliers)

    # ── Products ────────────────────────────────────────────
    products = [
        Product(sku_code="FMCG-001", name="Toor Dal 1kg", normalized_name="toor dal 1kg", category="FMCG", unit="kg", hsn_code="0713"),
        Product(sku_code="FMCG-002", name="Basmati Rice 5kg", normalized_name="basmati rice 5kg", category="FMCG", unit="kg", hsn_code="1006"),
        Product(sku_code="FMCG-003", name="Sunflower Oil 1L", normalized_name="sunflower oil 1l", category="FMCG", unit="litre", hsn_code="1512"),
        Product(sku_code="ELEC-001", name="USB-C Cable 1m", normalized_name="usb c cable 1m", category="Electronics", unit="piece", hsn_code="8544"),
        Product(sku_code="ELEC-002", name="LED Bulb 9W", normalized_name="led bulb 9w", category="Electronics", unit="piece", hsn_code="8539"),
        Product(sku_code="FOOD-001", name="Organic Honey 500g", normalized_name="organic honey 500g", category="Food", unit="g", hsn_code="0409"),
    ]
    session.add_all(products)

    # ── Commit ──────────────────────────────────────────────
    session.commit()
    session.close()

    print("✅ Seed data inserted successfully!")
    print(f"   Admin: admin@kosh.ai / Admin@123")
    print(f"   Test: test@test.com / Test@123")
    print(f"   Merchant: merchant1@example.com / Pass@123")
    print(f"   Merchant: merchant2@example.com / Pass@123")
    print(f"   Suppliers: {len(suppliers)}")
    print(f"   Products: {len(products)}")


if __name__ == "__main__":
    seed()
