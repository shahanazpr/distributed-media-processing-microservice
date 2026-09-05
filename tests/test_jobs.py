from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


@patch("app.api.jobs.S3Storage")
def test_create_job(mock_storage):
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


@patch("app.api.jobs.S3Storage")
def test_create_job_generates_unique_ids(mock_storage):
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


def test_create_job_rejects_invalid_operation():
    response = client.post(
        "/jobs",
        json={
            "filename": "image.jpg",
            "operation": "banana",
        },
    )

    assert response.status_code == 422