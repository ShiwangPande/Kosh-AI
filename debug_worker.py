import sys
import os

print(f"CWD: {os.getcwd()}")
print(f"PYTHONPATH: {sys.path}")

try:
    print("Attempting to import backend.config...")
    import backend.config
    print("Successfully imported backend.config")

    print("Attempting to import backend.workers.celery_app...")
    import backend.workers.celery_app
    print("Successfully imported backend.workers.celery_app")

    print("Attempting to import backend.database...")
    import backend.database
    print("Successfully imported backend.database")
    print(f"backend.database has Base: {hasattr(backend.database, 'Base')}")

    print("Attempting to import backend.models.models...")
    import backend.models.models
    print("Successfully imported backend.models.models")

    print("Attempting to import backend.workers.ocr_worker...")
    import backend.workers.ocr_worker
    print("Successfully imported backend.workers.ocr_worker")

except Exception as e:
    import traceback
    traceback.print_exc()
