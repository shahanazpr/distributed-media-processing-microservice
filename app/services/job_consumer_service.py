import json
from pika.exceptions import AMQPConnectionError

from app.core.rabbitmq_client import get_rabbitmq_connection, declare_queue, QUEUE_NAME


class JobConsumeError(Exception):
    """Raised when consuming a job message fails."""
    pass


def consume_one_job(timeout: int = 5) -> dict | None:
    """
    Pull a single job message off the queue (blocking, with timeout).
    Returns the parsed message dict, or None if the queue was empty.
    Intended for verification/testing — Celery will handle real consumption.
    """
    try:
        conn = get_rabbitmq_connection()
        channel = conn.channel()
        declare_queue(channel)

        method_frame, header_frame, body = channel.basic_get(
            queue=QUEUE_NAME, auto_ack=True
        )
        conn.close()
    except AMQPConnectionError as e:
        raise JobConsumeError(f"Failed to consume job: {e}") from e

    if method_frame is None:
        return None
    return json.loads(body)