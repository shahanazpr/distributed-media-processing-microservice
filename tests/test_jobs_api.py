from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_get_job_status(monkeypatch):
    job = {
        "job_id": "test-job-1",
        "filename": "image.jpg",
        "operation": "resize",
        "status": "COMPLETED",
        "created_at": "2026-09-01T10:00:00+00:00",
        "updated_at": "2026-09-01T10:05:00+00:00",
        "error": None,
        "output": {
            "filename": "resized_image.jpg"
        }
    }

    monkeypatch.setattr(
        "app.api.jobs.get_job",
        lambda job_id: job
    )

    response = client.get("/jobs/test-job-1")

    assert response.status_code == 200
    assert response.json() == job


def test_get_unknown_job(monkeypatch):
    monkeypatch.setattr(
        "app.api.jobs.get_job",
        lambda job_id: None
    )

    response = client.get("/jobs/unknown-job")

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_redis_failure(monkeypatch):
    from app.services.job_status_service import JobStatusError

    def raise_error(job_id):
        raise JobStatusError("Redis unavailable")

    monkeypatch.setattr(
        "app.api.jobs.get_job",
        raise_error
    )

    response = client.get("/jobs/test-job-1")

    assert response.status_code == 503
    assert response.json()["detail"] == "Job status service unavailable"