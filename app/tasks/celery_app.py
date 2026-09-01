import os

from celery import Celery


RABBITMQ_URL = os.getenv(
    "CELERY_BROKER_URL",
    "amqp://guest:guest@localhost:5672//",
)

REDIS_URL = os.getenv(
    "CELERY_RESULT_BACKEND",
    "redis://localhost:6379/0",
)


celery_app = Celery(
    "media_processing",
    broker=RABBITMQ_URL,
    backend=REDIS_URL,
    include=["app.tasks.tasks"],
)


celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)