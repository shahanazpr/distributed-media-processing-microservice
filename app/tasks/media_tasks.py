from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True)
def test_media_processing(self, message: str):
    print(f"Processing media task: {message}")
    return {
        "status": "completed",
        "message": message,
    }

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True)
def process_media(self, job_id: str):
    """
    Placeholder for the real media-processing task.
    TODO(Issue #15): implement actual S3 download, Pillow/FFmpeg processing,
    S3 upload, and Redis status updates.
    """
    raise NotImplementedError("process_media is not yet implemented — see Issue #15")