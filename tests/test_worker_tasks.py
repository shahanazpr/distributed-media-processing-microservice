from unittest.mock import MagicMock, patch

import pytest

from app.worker.tasks import process_media


def make_job(filename, object_key="inputs/test-file"):
    return {
        "job_id": "job-123",
        "filename": filename,
        "object_key": object_key,
        "operation": "process",
        "status": "PENDING",
    }


@patch("app.worker.tasks.S3Storage")
@patch("app.worker.tasks.JobStore")
@patch("app.worker.tasks.validate_image")
def test_process_image_job(
    mock_validate_image,
    mock_job_store,
    mock_storage,
    tmp_path,
):
    job_store = mock_job_store.return_value
    storage = mock_storage.return_value

    job_store.get_job.return_value = make_job("photo.jpg")

    mock_image = MagicMock()
    mock_validate_image.return_value = mock_image

    result = process_media.run("job-123")

    assert result["job_id"] == "job-123"
    assert result["status"] == "COMPLETED"

    job_store.update_status.assert_any_call(
        "job-123",
        "PROCESSING",
    )

    job_store.update_status.assert_any_call(
        "job-123",
        "COMPLETED",
    )

    storage.download_file.assert_called_once()
    storage.upload_file.assert_called_once()


@patch("app.worker.tasks.S3Storage")
@patch("app.worker.tasks.JobStore")
@patch("app.worker.tasks.FFmpegProcessor")
def test_process_video_job(
    mock_ffmpeg,
    mock_job_store,
    mock_storage,
):
    job_store = mock_job_store.return_value
    storage = mock_storage.return_value
    processor = mock_ffmpeg.return_value

    job_store.get_job.return_value = make_job(
        "video.mp4",
        "inputs/video.mp4",
    )

    processor.process.return_value = {
        "video": "/tmp/optimized.mp4",
        "thumbnail": "/tmp/thumbnail.jpg",
    }

    result = process_media.run("job-123")

    assert result["job_id"] == "job-123"
    assert result["status"] == "COMPLETED"

    processor.process.assert_called_once()

    assert storage.upload_file.call_count == 2

    job_store.update_status.assert_any_call(
        "job-123",
        "PROCESSING",
    )

    job_store.update_status.assert_any_call(
        "job-123",
        "COMPLETED",
    )


@patch("app.worker.tasks.JobStore")
def test_job_not_found(mock_job_store):
    job_store = mock_job_store.return_value
    job_store.get_job.return_value = None

    with pytest.raises(ValueError, match="Job not found"):
        process_media.run("missing-job")


@patch("app.worker.tasks.S3Storage")
@patch("app.worker.tasks.JobStore")
def test_unsupported_media_marks_job_failed(
    mock_job_store,
    mock_storage,
):
    job_store = mock_job_store.return_value
    job_store.get_job.return_value = make_job("document.pdf")

    with pytest.raises(ValueError, match="Unsupported media type"):
        process_media.run("job-123")

    job_store.update_status.assert_any_call(
        "job-123",
        "PROCESSING",
    )

    job_store.update_status.assert_any_call(
        "job-123",
        "FAILED",
    )