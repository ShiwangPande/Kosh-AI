import sqlalchemy
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://neondb_owner:npg_6hw1VJIFzWCu@ep-sparkling-bird-aivv4fqk-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require"

def migrate():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Checking for ocr_task_id column...")
        try:
            conn.execute(text("ALTER TABLE invoices ADD COLUMN ocr_task_id VARCHAR(100)"))
            conn.commit()
            print("Column ocr_task_id added successfully.")
        except Exception as e:
            if "already exists" in str(e):
                print("Column ocr_task_id already exists.")
            else:
                print(f"Error: {e}")

if __name__ == "__main__":
    migrate()
