import json
from datetime import datetime, timezone
from typing import Optional
from redis.exceptions import RedisError

from app.core.redis_client import get_redis_client

JOB_KEY_PREFIX = "job:"


class JobStatusError(Exception):
    """Raised when a job status operation fails."""
    pass


def _job_key(job_id: str) -> str:
    return f"{JOB_KEY_PREFIX}{job_id}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_job(job_id: str, filename: str, operation: str) -> dict:
    """Create a new job record with PENDING status."""
    job_data = {
        "job_id": job_id,
        "filename": filename,
        "operation": operation,
        "status": "PENDING",
        "created_at": _now(),
        "updated_at": _now(),
        "error": None,
        "output": None,
    }
    try:
        client = get_redis_client()
        client.set(_job_key(job_id), json.dumps(job_data))
    except RedisError as e:
        raise JobStatusError(f"Failed to create job {job_id}: {e}") from e

    return job_data


def get_job(job_id: str) -> Optional[dict]:
    """Retrieve job data by job_id. Returns None if not found."""
    try:
        client = get_redis_client()
        raw = client.get(_job_key(job_id))
    except RedisError as e:
        raise JobStatusError(f"Failed to retrieve job {job_id}: {e}") from e

    if raw is None:
        return None
    return json.loads(raw)