from app.worker.celery_app import celery_app


@celery_app.task
def process_media(job_id: str) -> dict:
    """Process a media job asynchronously."""
    return {
        "job_id": job_id,
        "status": "COMPLETED",
    }