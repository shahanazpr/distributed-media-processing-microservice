from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@patch("app.api.jobs.JobStore")
@patch("app.api.jobs.S3Storage")
def test_create_job(mock_storage, mock_job_store):
    mock_storage.return_value.generate_presigned_upload_url.return_value = (
        "https://example.com/presigned-url"
    )

    response = client.post(
        "/jobs",
        json={
            "filename": "image.jpg",
            "operation": "resize",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "job_id" in data
    assert data["status"] == "pending"
    assert data["filename"] == "image.jpg"
    assert data["operation"] == "resize"
    assert data["upload_url"] == "https://example.com/presigned-url"
    assert data["object_key"].startswith("uploads/")
    assert data["object_key"].endswith("/image.jpg")

    mock_storage.return_value.generate_presigned_upload_url.assert_called_once_with(
        data["object_key"]
    )

    mock_job_store.return_value.create_job.assert_called_once_with(
        job_id=data["job_id"],
        filename="image.jpg",
        operation="resize",
        object_key=data["object_key"],
        status="pending",
    )


@patch("app.api.jobs.JobStore")
@patch("app.api.jobs.S3Storage")
def test_create_job_generates_unique_ids(mock_storage, mock_job_store):
    mock_storage.return_value.generate_presigned_upload_url.return_value = (
        "https://example.com/presigned-url"
    )

    response1 = client.post(
        "/jobs",
        json={
            "filename": "image.jpg",
            "operation": "resize",
        },
    )

    response2 = client.post(
        "/jobs",
        json={
            "filename": "image.jpg",
            "operation": "resize",
        },
    )

    assert response1.status_code == 200
    assert response2.status_code == 200

    data1 = response1.json()
    data2 = response2.json()

    assert data1["job_id"] != data2["job_id"]
    assert data1["object_key"] != data2["object_key"]


@patch("app.api.jobs.JobStore")
def test_get_job(mock_job_store):
    mock_job_store.return_value.get_job.return_value = {
        "job_id": "test-job-id",
        "status": "pending",
        "filename": "image.jpg",
        "operation": "resize",
        "object_key": "uploads/test-job-id/image.jpg",
    }

    response = client.get("/jobs/test-job-id")

    assert response.status_code == 200

    data = response.json()

    assert data["job_id"] == "test-job-id"
    assert data["status"] == "pending"
    assert data["filename"] == "image.jpg"
    assert data["operation"] == "resize"
    assert data["object_key"] == "uploads/test-job-id/image.jpg"

    mock_job_store.return_value.get_job.assert_called_once_with(
        "test-job-id"
    )


@patch("app.api.jobs.JobStore")
def test_get_job_not_found(mock_job_store):
    mock_job_store.return_value.get_job.return_value = None

    response = client.get("/jobs/non-existent")

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"

    mock_job_store.return_value.get_job.assert_called_once_with(
        "non-existent"
    )


def test_create_job_rejects_invalid_operation():
    response = client.post(
        "/jobs",
        json={
            "filename": "image.jpg",
            "operation": "banana",
        },
    )

    assert response.status_code == 422