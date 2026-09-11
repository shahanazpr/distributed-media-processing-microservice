import json
import pytest
from unittest.mock import MagicMock, patch
from redis.exceptions import ConnectionError as RedisConnectionError

from app.services import job_status_service as svc


@pytest.fixture
def mock_redis():
    with patch("app.services.job_status_service.get_redis_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        yield mock_client


def test_create_job(mock_redis):
    job = svc.create_job("job-1", "image.jpg", "resize")

    assert job["job_id"] == "job-1"
    assert job["status"] == "PENDING"
    assert job["filename"] == "image.jpg"
    mock_redis.set.assert_called_once()

    key, value = mock_redis.set.call_args[0]
    assert key == "job:job-1"
    assert json.loads(value)["status"] == "PENDING"


def test_get_job_found(mock_redis):
    stored = json.dumps({"job_id": "job-1", "status": "PENDING"})
    mock_redis.get.return_value = stored

    job = svc.get_job("job-1")

    assert job["job_id"] == "job-1"
    mock_redis.get.assert_called_once_with("job:job-1")


def test_get_job_not_found(mock_redis):
    mock_redis.get.return_value = None
    job = svc.get_job("missing-job")
    assert job is None


def test_update_job_status_to_completed(mock_redis):
    existing = json.dumps({
        "job_id": "job-1", "status": "PROCESSING",
        "error": None, "output": None,
    })
    mock_redis.get.return_value = existing

    updated = svc.update_job_status(
        "job-1", "COMPLETED", output={"url": "https://cdn/output.jpg"}
    )

    assert updated["status"] == "COMPLETED"
    assert updated["output"]["url"] == "https://cdn/output.jpg"


def test_update_job_status_to_failed(mock_redis):
    existing = json.dumps({
        "job_id": "job-1", "status": "PROCESSING",
        "error": None, "output": None,
    })
    mock_redis.get.return_value = existing

    updated = svc.update_job_status("job-1", "FAILED", error="S3 timeout")

    assert updated["status"] == "FAILED"
    assert updated["error"] == "S3 timeout"


def test_update_job_not_found_raises(mock_redis):
    mock_redis.get.return_value = None
    with pytest.raises(svc.JobStatusError):
        svc.update_job_status("missing-job", "PROCESSING")

        
def test_create_job_redis_down(mock_redis):
    mock_redis.set.side_effect = RedisConnectionError("Connection refused")
    with pytest.raises(svc.JobStatusError):
        svc.create_job("job-1", "image.jpg", "resize")