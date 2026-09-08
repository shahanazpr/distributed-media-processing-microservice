from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


@patch("app.api.jobs.JobStore")
def test_get_job_status(mock_job_store):
    job = {
        "job_id": "test-job-1",
        "filename": "image.jpg",
        "operation": "resize",
        "status": "completed",
        "created_at": "2026-09-01T10:00:00+00:00",
        "updated_at": "2026-09-01T10:05:00+00:00",
        "error": None,
        "output": {
            "filename": "resized_image.jpg"
        },
    }

    mock_job_store.return_value.get_job.return_value = job

    response = client.get("/jobs/test-job-1")

    assert response.status_code == 200

    data = response.json()

    assert data["job_id"] == "test-job-1"
    assert data["status"] == "completed"
    assert data["filename"] == "image.jpg"
    assert data["operation"] == "resize"
    assert data["output"]["filename"] == "resized_image.jpg"

    mock_job_store.return_value.get_job.assert_called_once_with(
        "test-job-1"
    )


@patch("app.api.jobs.JobStore")
def test_get_unknown_job(mock_job_store):
    mock_job_store.return_value.get_job.return_value = None

    response = client.get("/jobs/unknown-job")

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"

    mock_job_store.return_value.get_job.assert_called_once_with(
        "unknown-job"
    )


@patch("app.api.jobs.JobStore")
def test_redis_failure(mock_job_store):
    mock_job_store.return_value.get_job.side_effect = Exception(
        "Redis unavailable"
    )

    failing_client = TestClient(
        app,
        raise_server_exceptions=False,
    )

    response = failing_client.get("/jobs/test-job-1")

    assert response.status_code == 500
