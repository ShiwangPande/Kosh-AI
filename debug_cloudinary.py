
import psycopg2
import os
import cloudinary
import cloudinary.api
from backend.config import get_settings

settings = get_settings()

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True
)

try:
    print("Connecting to DB...")
    conn = psycopg2.connect('postgresql://kosh:kosh_secret@db:5432/kosh_ai')
    cur = conn.cursor()
    cur.execute('SELECT file_key FROM invoices ORDER BY created_at DESC LIMIT 1')
    res = cur.fetchone()
    if not res:
        print("No invoices found.")
        exit(0)
        
    file_key = res[0]
    print(f'Checking KEY: {file_key}')

    try:
        res = cloudinary.api.resource(file_key)
        print('--- FOUND (As-is) ---')
        print(f'Type: {res.get("resource_type")}')
        print(f'Format: {res.get("format")}')
        print(f'Public ID: {res.get("public_id")}')
    except Exception as e:
        print(f'Not found as-is: {e}')
        
    try:
        # Try appending .pdf
        res = cloudinary.api.resource(file_key + '.pdf')
        print('--- FOUND (+.pdf) ---')
        print(f'Type: {res.get("resource_type")}')
        print(f'Format: {res.get("format")}')
        print(f'Public ID: {res.get("public_id")}')
    except Exception as e:
        print(f'Not found (+.pdf): {e}')

except Exception as e:
    print(f"Error: {e}")
