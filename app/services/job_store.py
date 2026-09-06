import json
import os

import redis

from app.core import config


class JobStore:
    def __init__(self, client=None):
        self.client = client or redis.from_url(
            os.getenv(
                "REDIS_URL",
                "redis://localhost:6379/0",
            ),
            decode_responses=True,
        )

    def create_job(
        self,
        job_id: str,
        filename: str,
        operation: str,
        object_key: str,
        status: str = "pending",
    ) -> None:
        job = {
            "job_id": job_id,
            "status": status,
            "filename": filename,
            "operation": operation,
            "object_key": object_key,
        }

        self.client.set(
            f"job:{job_id}",
            json.dumps(job),
        )

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
        job = self.get_job(job_id)

        if job is None:
            return None

        job["status"] = status

        self.client.set(
            f"job:{job_id}",
            json.dumps(job),
        )

        return job