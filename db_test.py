import sqlalchemy
from sqlalchemy import create_engine, text
import time

DATABASE_URL = "postgresql://neondb_owner:npg_6hw1VJIFzWCu@ep-sparkling-bird-aivv4fqk-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require"

def check_db():
    engine = create_engine(DATABASE_URL)
    try:
        with engine.connect() as conn:
            print("Successfully connected to DB.")
            
            start = time.time()
            result = conn.execute(text("SELECT count(*) FROM invoices"))
            count = result.fetchone()[0]
            print(f"Invoice count: {count} (took {time.time() - start:.2f}s)")
            
            start = time.time()
            result = conn.execute(text("SELECT * FROM invoices LIMIT 5"))
            rows = result.fetchall()
            print(f"Fetched 5 invoices (took {time.time() - start:.2f}s)")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
