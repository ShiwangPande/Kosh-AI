"""Kaggle Data Import Script (Optimized)"""
import csv
import asyncio
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database import async_session_factory
from backend.models.models import Product, Supplier, Score, Merchant
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CSV_PATH = "database/product_sales_dataset_final.csv"
MERCHANT_ID = UUID("d5fd7962-d36c-42cf-f172-4b859d7d2459")
LIMIT = 5000

async def import_kaggle_data():
    async with async_session_factory() as db:
        # Verify merchant
        res = await db.execute(select(Merchant).where(Merchant.id == MERCHANT_ID))
        if not res.scalar_one_or_none():
            logger.error(f"Merchant {MERCHANT_ID} not found.")
            return

        # Local caches
        product_cache = {} # name -> id
        supplier_cache = {} # supplier_name -> id

        with open(CSV_PATH, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            reader.fieldnames = [name.strip() for name in reader.fieldnames]
            
            count = 0
            for row in reader:
                if count >= LIMIT:
                    break
                
                try:
                    product_name = row['Product_Name'].strip()
                    category = row['Category'].strip()
                    region = row['Region'].strip()
                    city = row['City'].strip()
                    state = row['State'].strip()
                    unit_price = float(row['Unit_Price'])
                except (KeyError, ValueError) as e:
                    logger.warning(f"Skipping row due to error: {e}")
                    continue

                # 1. Product
                if product_name not in product_cache:
                    prod_res = await db.execute(select(Product).where(Product.name == product_name))
                    prod = prod_res.scalar_one_or_none()
                    if not prod:
                        prod = Product(
                            name=product_name,
                            normalized_name=product_name.lower(),
                            category=category,
                            unit="unit"
                        )
                        db.add(prod)
                        await db.flush()
                    product_cache[product_name] = prod.id
                
                product_id = product_cache[product_name]

                # 2. Supplier (Mocked by Region)
                supplier_name = f"{region} Regional Wholesale"
                if supplier_name not in supplier_cache:
                    supp_res = await db.execute(select(Supplier).where(Supplier.name == supplier_name))
                    supp = supp_res.scalar_one_or_none()
                    if not supp:
                        supp = Supplier(
                            name=supplier_name,
                            contact_person=f"{region} Distribution Mgr",
                            city=city,
                            state=state,
                            category=category,
                            is_approved=True,
                            reliability_score=0.85 + (count % 15) / 100, # Variable reliability
                            avg_delivery_days=2.0 + (count % 5),
                            credit_terms=30
                        )
                        db.add(supp)
                        await db.flush()
                    supplier_cache[supplier_name] = supp.id
                
                supplier_id = supplier_cache[supplier_name]

                # 3. Market Score
                # Always create/update a score for this merchant/product/supplier
                score_res = await db.execute(
                    select(Score).where(
                        Score.merchant_id == MERCHANT_ID,
                        Score.product_id == product_id,
                        Score.supplier_id == supplier_id
                    )
                )
                score = score_res.scalar_one_or_none()
                if not score:
                    score = Score(
                        merchant_id=MERCHANT_ID,
                        supplier_id=supplier_id,
                        product_id=product_id,
                        price_score=1.0, 
                        reliability_score=0.9,
                        delivery_speed=0.9,
                        credit_score=0.8,
                        switching_friction=0.2,
                        total_score=0.85,
                    )
                    db.add(score)
                
                # Update price (mocking a dynamic market)
                score.price_score = 1.0 / (unit_price/100.0) if unit_price > 0 else 0 
                # Total score simplified
                score.total_score = (score.price_score * 0.4) + (score.reliability_score * 0.3)
                
                count += 1
                if count % 200 == 0:
                    logger.info(f"Ingested {count} rows...")
                    await db.commit()

            await db.commit()
            logger.info(f"Ingestion complete! {count} market data points added.")

if __name__ == "__main__":
    asyncio.run(import_kaggle_data())
