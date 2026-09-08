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
    print(f"Processing media job: {job_id}")

    return {
        "status": "completed",
        "job_id": job_id,
    }