"""
Static analysis test to enforce concurrency safety rules in workers.
"""
import pytest
import os
import ast

WORKER_DIR = "backend/workers"

def get_worker_files():
    files = []
    for root, _, filenames in os.walk(WORKER_DIR):
        for filename in filenames:
            if filename.endswith(".py") and filename != "__init__.py" and filename != "celery_app.py":
                files.append(os.path.join(root, filename))
    return files

def check_file_content(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    tree = ast.parse(content)
    
    violations = []
    
    # 1. check for manual event loops
    if "get_event_loop()" in content or "new_event_loop()" in content:
         violations.append("Manual event loop detected (use asyncio.run).")

    # 2. check for run_until_complete
    if "run_until_complete" in content:
        violations.append("run_until_complete detected (use asyncio.run).")
        
    # 3. check for SessionLocal in async def
    # This is a bit harder to strictly parse without semantic analysis, 
    # but we can look for "SessionLocal" string usage in file as a smoke test
    # if the file contains "async def".
    if "async def" in content and "SessionLocal" in content:
        violations.append("SessionLocal imported/used in async worker (use async_session_factory).")

    # 4. Check for create_engine (sync)
    if "create_engine" in content and "backend.database" not in content:
         # crude check allowing imports from backend.database but not direct usage? 
         # actually "create_engine" is sync. 
         if "create_engine(" in content:
             violations.append("Direct create_engine() call detected (use backend.database).")

    return violations

def test_worker_safety():
    worker_files = get_worker_files()
    if not worker_files:
        pytest.skip("No worker files found")

    all_violations = {}
    for f in worker_files:
        violations = check_file_content(f)
        if violations:
            all_violations[f] = violations

    if all_violations:
        error_msg = "\nCONCURRENCY VIOLATIONS FOUND:\n"
        for f, v_list in all_violations.items():
            error_msg += f"\nFile: {f}\n"
            for v in v_list:
                error_msg += f"  - {v}\n"
        
        pytest.fail(error_msg)
