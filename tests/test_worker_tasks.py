from unittest.mock import MagicMock, patch

import pytest

from app.tasks.media_tasks import process_media


def make_job(filename, object_key="inputs/test-file"):
    return {
        "job_id": "job-123",
        "filename": filename,
        "object_key": object_key,
        "operation": "process",
        "status": "pending",
    }


@patch("app.tasks.media_tasks.S3Storage")
@patch("app.tasks.media_tasks.JobStore")
@patch("app.tasks.media_tasks.validate_image")
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
    assert result["status"] == "completed"

    job_store.update_status.assert_any_call(
        "job-123",
        "processing",
    )

    job_store.update_job.assert_called_once()
    update_call = job_store.update_job.call_args

    assert update_call.kwargs["job_id"] == "job-123"
    assert update_call.kwargs["status"] == "completed"
    assert update_call.kwargs["output"] is not None

    storage.download_file.assert_called_once()
    storage.upload_file.assert_called_once()


@patch("app.tasks.media_tasks.S3Storage")
@patch("app.tasks.media_tasks.JobStore")
@patch("app.tasks.media_tasks.FFmpegProcessor")
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
    assert result["status"] == "completed"

    processor.process.assert_called_once()

    assert storage.upload_file.call_count == 2

    job_store.update_status.assert_any_call(
        "job-123",
        "processing",
    )

    job_store.update_job.assert_called_once()
    update_call = job_store.update_job.call_args

    assert update_call.kwargs["job_id"] == "job-123"
    assert update_call.kwargs["status"] == "completed"
    assert update_call.kwargs["output"] is not None


@patch("app.tasks.media_tasks.JobStore")
def test_job_not_found(mock_job_store):
    job_store = mock_job_store.return_value
    job_store.get_job.return_value = None

    with pytest.raises(ValueError, match="Job not found"):
        process_media.run("missing-job")


@patch("app.tasks.media_tasks.S3Storage")
@patch("app.tasks.media_tasks.JobStore")
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
        "processing",
    )

    job_store.update_job.assert_called_once()
    update_call = job_store.update_job.call_args

    assert update_call.kwargs["job_id"] == "job-123"
    assert update_call.kwargs["status"] == "failed"
    assert update_call.kwargs["error"] is not None