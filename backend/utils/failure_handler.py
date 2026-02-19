"""Failure handling — Dead Letter Queue, retry policies, circuit breaker, timeout management."""
import time
import json
import logging
from typing import Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass, field, asdict

import redis

from backend.config import get_settings

settings = get_settings()
logger = logging.getLogger("kosh.failure")


# ── Retry Policy ───────────────────────────────────────────

class RetryPolicy:
    """Configurable retry policy with exponential backoff."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 60.0,     # seconds
        backoff_multiplier: float = 2.0,
        max_delay: float = 3600.0,       # 1 hour cap
        retryable_exceptions: tuple = (Exception,),
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_multiplier = backoff_multiplier
        self.max_delay = max_delay
        self.retryable_exceptions = retryable_exceptions

    def get_delay(self, attempt: int) -> float:
        delay = self.initial_delay * (self.backoff_multiplier ** attempt)
        return min(delay, self.max_delay)

    def should_retry(self, attempt: int, exception: Exception) -> bool:
        if attempt >= self.max_retries:
            return False
        return isinstance(exception, self.retryable_exceptions)


# Default policies for different task types
OCR_RETRY_POLICY = RetryPolicy(
    max_retries=3,
    initial_delay=30,
    backoff_multiplier=2.0,
    max_delay=600,  # 10 min cap
)

NOTIFICATION_RETRY_POLICY = RetryPolicy(
    max_retries=5,
    initial_delay=10,
    backoff_multiplier=1.5,
    max_delay=300,
)


# ── Dead Letter Queue ─────────────────────────────────────

class DeadLetterQueue:
    """Redis-backed dead letter queue for failed tasks."""

    DLQ_KEY = "kosh:dlq"
    DLQ_STATS_KEY = "kosh:dlq:stats"

    def __init__(self, redis_url: str = None):
        self._redis_url = redis_url or settings.REDIS_URL
        self._client = None

    def _get_client(self):
        if self._client is None:
            self._client = redis.from_url(self._redis_url, decode_responses=True)
        return self._client

    def push(
        self,
        task_name: str,
        task_args: Dict[str, Any],
        error: str,
        retry_count: int,
        original_id: Optional[str] = None,
    ):
        """Push a failed task to the dead letter queue."""
        entry = {
            "task_name": task_name,
            "task_args": task_args,
            "error": str(error)[:2000],  # Truncate long errors
            "retry_count": retry_count,
            "original_id": original_id,
            "failed_at": time.time(),
            "status": "pending",
        }
        r = self._get_client()
        r.lpush(self.DLQ_KEY, json.dumps(entry))
        r.hincrby(self.DLQ_STATS_KEY, "total", 1)
        r.hincrby(self.DLQ_STATS_KEY, f"task:{task_name}", 1)

        logger.error(f"DLQ: Task {task_name} pushed after {retry_count} retries. "
                     f"Error: {error}")

    def pop(self) -> Optional[Dict]:
        """Pop the oldest failed task from the queue."""
        r = self._get_client()
        data = r.rpop(self.DLQ_KEY)
        if data:
            return json.loads(data)
        return None

    def peek(self, count: int = 10) -> list:
        """View items without removing them."""
        r = self._get_client()
        items = r.lrange(self.DLQ_KEY, 0, count - 1)
        return [json.loads(i) for i in items]

    def size(self) -> int:
        r = self._get_client()
        return r.llen(self.DLQ_KEY)

    def stats(self) -> dict:
        r = self._get_client()
        raw = r.hgetall(self.DLQ_STATS_KEY)
        return {k: int(v) for k, v in raw.items()}

    def requeue(self, task_name: str = None) -> int:
        """Move items back to processing queue for retry."""
        from backend.workers.celery_app import celery_app

        count = 0
        while True:
            entry = self.pop()
            if entry is None:
                break
            if task_name and entry["task_name"] != task_name:
                # Put it back
                r = self._get_client()
                r.rpush(self.DLQ_KEY, json.dumps(entry))
                continue

            celery_app.send_task(
                entry["task_name"],
                args=list(entry["task_args"].values()) if isinstance(entry["task_args"], dict)
                     else entry["task_args"],
            )
            count += 1

        logger.info(f"DLQ: Requeued {count} tasks")
        return count


# ── Circuit Breaker ────────────────────────────────────────

class CircuitState(Enum):
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing — reject requests
    HALF_OPEN = "half_open" # Testing if service recovered


class CircuitBreaker:
    """Protect external services (OCR API, S3) with circuit breaker pattern."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,  # seconds before trying again
        success_threshold: int = 2,       # successes needed to close circuit
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0

    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.info(f"Circuit [{self.name}]: OPEN → HALF_OPEN")
                return True
            return False
        # HALF_OPEN
        return True

    def record_success(self):
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info(f"Circuit [{self.name}]: HALF_OPEN → CLOSED")
        else:
            self.failure_count = max(0, self.failure_count - 1)

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit [{self.name}]: HALF_OPEN → OPEN")
        elif self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit [{self.name}]: CLOSED → OPEN "
                          f"({self.failure_count} failures)")


# ── Global circuit breakers ────────────────────────────────
ocr_circuit = CircuitBreaker("ocr_api", failure_threshold=5, recovery_timeout=120)
s3_circuit = CircuitBreaker("s3_storage", failure_threshold=3, recovery_timeout=60)


# ── Timeout wrapper ────────────────────────────────────────

class TaskTimeout:
    """Context manager for task-level timeouts."""

    def __init__(self, seconds: float, task_name: str = "unknown"):
        self.seconds = seconds
        self.task_name = task_name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, *args):
        elapsed = time.time() - self.start_time
        if elapsed > self.seconds:
            logger.warning(f"Task [{self.task_name}] exceeded timeout: "
                          f"{elapsed:.1f}s > {self.seconds}s")

    @property
    def elapsed(self) -> float:
        return time.time() - self.start_time if self.start_time else 0

    @property
    def remaining(self) -> float:
        return max(0, self.seconds - self.elapsed)

    def check(self):
        """Raise if timeout exceeded."""
        if self.elapsed > self.seconds:
            raise TimeoutError(
                f"Task [{self.task_name}] timed out after {self.elapsed:.1f}s "
                f"(limit: {self.seconds}s)"
            )


# Singleton DLQ instance
dlq = DeadLetterQueue()
