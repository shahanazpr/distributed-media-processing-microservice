import json
from redis.exceptions import RedisError  # noqa: F401 (kept for parity if needed later)
from pika.exceptions import AMQPConnectionError

from app.core.rabbitmq_client import get_rabbitmq_connection, declare_queue, QUEUE_NAME


class JobPublishError(Exception):
    """Raised when a job message fails to publish."""
    pass


def publish_job(job_id: str, filename: str, operation: str, input_location: str) -> dict:
    """Publish a media-processing job message to the queue."""
    message = {
        "job_id": job_id,
        "filename": filename,
        "operation": operation,
        "input_location": input_location,
    }

    try:
        conn = get_rabbitmq_connection()
        channel = conn.channel()
        declare_queue(channel)

        channel.basic_publish(
            exchange="",
            routing_key=QUEUE_NAME,
            body=json.dumps(message),
            properties=None,
        )
        conn.close()
    except AMQPConnectionError as e:
        raise JobPublishError(f"Failed to publish job {job_id}: {e}") from e

    return message