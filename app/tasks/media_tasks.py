from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True)
def test_media_processing(self, message: str):
    print(f"Processing media task: {message}")
    return {
        "status": "completed",
        "message": message,
    }