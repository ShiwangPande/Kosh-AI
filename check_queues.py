import redis
try:
    r = redis.Redis(host='localhost', port=6379, db=1)
    print(f"Celery queue size: {r.llen('celery')}")
    print(f"OCR queue size: {r.llen('ocr')}")
except Exception as e:
    print(f"Error connecting to Redis: {e}")
