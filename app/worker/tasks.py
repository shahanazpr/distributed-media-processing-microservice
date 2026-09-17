from app.worker.celery_app import celery_app


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=False,
    retry_kwargs={"max_retries": 3},
)
def process_media(self, job_id: str) -> dict:
    """Process a media job asynchronously."""

    return {
        "job_id": job_id,
        "status": "COMPLETED",
    }