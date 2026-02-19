
import os
import uuid
from sqlalchemy import create_engine, Column
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import UUID

# Hardcode to match worker config
DB_URL = os.getenv("DATABASE_URL_SYNC", "postgresql://kosh:kosh_secret@db:5432/kosh_ai")
Base = declarative_base()

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

try:
    print(f"Connecting to {DB_URL}...")
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    target_id_str = "7343f691-16ec-4913-8c1d-858d22c8828c"
    print(f"Querying for ID (str): {target_id_str}")
    
    # Test 1: Query with string
    invoice = session.query(Invoice).filter(Invoice.id == target_id_str).first()
    if invoice:
        print("Success with STRING!")
    else:
        print("Failed with STRING")

    # Test 2: Query with UUID object
    target_id_uuid = uuid.UUID(target_id_str)
    print(f"Querying for ID (uuid): {target_id_uuid}")
    invoice_uuid = session.query(Invoice).filter(Invoice.id == target_id_uuid).first()
    if invoice_uuid:
        print("Success with UUID obj!")
    else:
        print("Failed with UUID obj")

except Exception as e:
    print(f"Error: {e}")
