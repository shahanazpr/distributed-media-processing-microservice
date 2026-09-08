from app.tasks.celery_app import celery_app


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def sample_processing_task(self, message: str):
    print(f"Processing task: {message}")

    return {
        "status": "completed",
        "message": message,
    }