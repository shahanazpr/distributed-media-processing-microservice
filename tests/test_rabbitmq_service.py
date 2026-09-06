import json
import pytest
from unittest.mock import MagicMock, patch

from app.services import job_publisher_service as pub_svc
from app.services import job_consumer_service as con_svc


@pytest.fixture
def mock_rabbitmq_connection():
    with patch("app.services.job_publisher_service.get_rabbitmq_connection") as mock_pub_conn, \
         patch("app.services.job_consumer_service.get_rabbitmq_connection") as mock_con_conn:
        mock_channel = MagicMock()
        mock_conn_obj = MagicMock()
        mock_conn_obj.channel.return_value = mock_channel

        mock_pub_conn.return_value = mock_conn_obj
        mock_con_conn.return_value = mock_conn_obj

        yield mock_channel


def test_publish_job(mock_rabbitmq_connection):
    message = pub_svc.publish_job(
        job_id="job-1",
        filename="image.jpg",
        operation="resize",
        input_location="s3://input-bucket/image.jpg",
    )

    assert message["job_id"] == "job-1"
    assert message["operation"] == "resize"
    mock_rabbitmq_connection.basic_publish.assert_called_once()

    call_kwargs = mock_rabbitmq_connection.basic_publish.call_args.kwargs
    published_body = json.loads(call_kwargs["body"])
    assert published_body["job_id"] == "job-1"


def test_consume_one_job_returns_message(mock_rabbitmq_connection):
    fake_body = json.dumps({"job_id": "job-1", "operation": "resize"}).encode()
    mock_rabbitmq_connection.basic_get.return_value = (MagicMock(), MagicMock(), fake_body)

    result = con_svc.consume_one_job()

    assert result["job_id"] == "job-1"


def test_consume_one_job_empty_queue(mock_rabbitmq_connection):
    mock_rabbitmq_connection.basic_get.return_value = (None, None, None)

    result = con_svc.consume_one_job()

    assert result is None


def test_publish_job_connection_failure():
    with patch("app.services.job_publisher_service.get_rabbitmq_connection") as mock_conn:
        from pika.exceptions import AMQPConnectionError
        mock_conn.side_effect = AMQPConnectionError("Connection refused")

        with pytest.raises(pub_svc.JobPublishError):
            pub_svc.publish_job("job-1", "image.jpg", "resize", "s3://bucket/image.jpg")