import redis
import sys

try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    print("Redis is running!")
except Exception as e:
    print(f"Redis is NOT running: {e}")
    sys.exit(1)
