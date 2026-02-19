import asyncio
import uuid
from backend.database import async_session_factory
from backend.models.models import Supplier, Product
from sqlalchemy import select

async def seed():
    async with async_session_factory() as session:
        # Check if suppliers exist
        res = await session.execute(select(Supplier))
        if res.scalars().first():
            print("Suppliers already exist. Skipping seed.")
            return

        suppliers = [
            Supplier(
                name="National Distributors Ltd",
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
                category="Food",
                city="Hyderabad",
                state="Telangana",
                credit_terms=15,
                avg_delivery_days=2,
                reliability_score=0.92,
                is_approved=True,
            ),
        ]
        session.add_all(suppliers)
        
        products = [
            Product(sku_code="FMCG-001", name="Toor Dal 1kg", normalized_name="toor dal 1kg", category="FMCG", unit="kg"),
            Product(sku_code="FMCG-002", name="Basmati Rice 5kg", normalized_name="basmati rice 5kg", category="FMCG", unit="kg"),
            Product(sku_code="ELEC-001", name="USB-C Cable 1m", normalized_name="usb c cable 1m", category="Electronics", unit="piece"),
        ]
        session.add_all(products)
        
        await session.commit()
        print("✅ Async seed successful!")

if __name__ == "__main__":
    asyncio.run(seed())
