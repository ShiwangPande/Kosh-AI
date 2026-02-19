import asyncio
from sqlalchemy import text
from backend.database import async_session_factory

TABLES_TO_CLEAR = [
    "activity_logs",
    "recommendation_feedback",
    "recommendations",
    "scores",
    "order_items",
    "orders",
    "invoice_items",
    "invoices",
    "products",
    "suppliers",
    "market_index",
    "aggregated_prices",
    "supplier_benchmarks",
    "market_trends",
    "risk_alerts",
    "price_predictions",
    "demand_predictions",
    "restock_predictions",
    "supplier_risk_predictions",
    "whatsapp_messages",
    "merchant_preferences",
]

async def reset_data():
    async with async_session_factory() as db:
        print("Starting comprehensive data reset...")
        # Use TRUNCATE with CASCADE to handle foreign key dependencies efficiently
        # We wrap in a transaction
        for table in TABLES_TO_CLEAR:
            try:
                print(f"Clearing table: {table}")
                await db.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
            except Exception as e:
                print(f"Warning: Could not clear {table}: {e}")
        
        await db.commit()
        print("Data reset complete. Merchant accounts and system settings were preserved.")

if __name__ == "__main__":
    asyncio.run(reset_data())
