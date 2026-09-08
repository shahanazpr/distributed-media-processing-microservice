import json
from datetime import datetime, timezone

import redis

from app.core.config import get_settings


class JobStore:
    def __init__(self, client=None):
        settings = get_settings()

        self.client = client or redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password or None,
            decode_responses=True,
        )

    def create_job(
        self,
        job_id: str,
        filename: str,
        operation: str,
        object_key: str,
        status: str = "pending",
    ) -> dict:
        now = datetime.now(timezone.utc).isoformat()

        job = {
            "job_id": job_id,
            "status": status,
            "filename": filename,
            "operation": operation,
            "object_key": object_key,
            "created_at": now,
            "updated_at": now,
            "error": None,
            "output": None,
        }

        self.client.set(
            f"job:{job_id}",
            json.dumps(job),
        )

        return job

    def get_job(self, job_id: str) -> dict | None:
        data = self.client.get(f"job:{job_id}")

        if data is None:
            return None

        return json.loads(data)

    def update_status(
        self,
        job_id: str,
        status: str,
    ) -> dict | None:
        return self.update_job(
            job_id=job_id,
            status=status,
        )

    def update_job(
        self,
        job_id: str,
        status: str | None = None,
        output: dict | None = None,
        error: str | None = None,
    ) -> dict | None:
        job = self.get_job(job_id)

        if job is None:
            return None

        if status is not None:
            job["status"] = status

        if output is not None:
            job["output"] = output

        if error is not None:
            job["error"] = error

        job["updated_at"] = datetime.now(timezone.utc).isoformat()

        self.client.set(
            f"job:{job_id}",
            json.dumps(job),
        )

        return job