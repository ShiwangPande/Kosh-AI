from backend.database import engine_sync
from sqlalchemy import text
with engine_sync.connect() as conn:
    r = conn.execute(text("SELECT id FROM merchants WHERE email = 'shiwangpande1@gmail.com'"))
    print(r.scalar())
