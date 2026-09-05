import pika
from app.core.config import get_settings

QUEUE_NAME = "media_processing_queue"


def get_rabbitmq_connection() -> pika.BlockingConnection:
    """Creates a new blocking connection to RabbitMQ using app settings."""
    settings = get_settings()
    credentials = pika.PlainCredentials(
        settings.rabbitmq_user, settings.rabbitmq_password
    )
    parameters = pika.ConnectionParameters(
        host=settings.rabbitmq_host,
        port=settings.rabbitmq_port,
        virtual_host=settings.rabbitmq_vhost,
        credentials=credentials,
    )
    return pika.BlockingConnection(parameters)


def declare_queue(channel) -> None:
    """Ensures the media-processing queue exists (idempotent)."""
    channel.queue_declare(queue=QUEUE_NAME, durable=True)