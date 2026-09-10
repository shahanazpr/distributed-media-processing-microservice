from pathlib import Path
from unittest.mock import patch

import pytest

from app.tasks.media_tasks import process_media


def make_job(
    filename="input.png",
    object_key="inputs/input.png",
):
    return {
        "job_id": "job-123",
        "filename": filename,
        "object_key": object_key,
        "operation": "resize",
        "status": "pending",
    }


@patch("app.tasks.media_tasks.ImageProcessor")
@patch("app.tasks.media_tasks.S3Storage")
@patch("app.tasks.media_tasks.JobStore")
def test_process_image_job(
    mock_job_store,
    mock_storage,
    mock_image_processor,
):
    job_store = mock_job_store.return_value
    storage = mock_storage.return_value
    processor = mock_image_processor.return_value

    job_store.get_job.return_value = make_job(
        "image.png",
        "inputs/image.png",
    )

    def fake_download(object_key, file_path):
        Path(file_path).write_bytes(b"fake image")

    def fake_process(input_path, output_path):
        Path(output_path).write_bytes(b"processed image")

    storage.download_file.side_effect = fake_download
    processor.process.side_effect = fake_process

    result = process_media.run("job-123")

    assert result["job_id"] == "job-123"
    assert result["status"] == "completed"
    assert result["output"]["type"] == "image"
    assert "object_key" in result["output"]

    storage.download_file.assert_called_once()
    storage.upload_file.assert_called_once()
    processor.process.assert_called_once()

    job_store.update_status.assert_called_with(
        "job-123",
        "processing",
    )

    job_store.update_job.assert_called_once()

    update_call = job_store.update_job.call_args

    assert update_call.args[0] == "job-123"
    assert update_call.kwargs["status"] == "completed"
    assert update_call.kwargs["output"] == result["output"]


@patch("app.tasks.media_tasks.FFmpegProcessor")
@patch("app.tasks.media_tasks.S3Storage")
@patch("app.tasks.media_tasks.JobStore")
def test_process_video_job(
    mock_job_store,
    mock_storage,
    mock_ffmpeg,
):
    job_store = mock_job_store.return_value
    storage = mock_storage.return_value
    processor = mock_ffmpeg.return_value

    job_store.get_job.return_value = make_job(
        "video.mp4",
        "inputs/video.mp4",
    )

    def fake_download(object_key, file_path):
        Path(file_path).write_bytes(b"fake video")

    def fake_process(input_path, output_dir):
        output_dir = Path(output_dir)

        video_path = output_dir / "optimized.mp4"
        thumbnail_path = output_dir / "thumbnail.jpg"

        video_path.write_bytes(b"processed video")
        thumbnail_path.write_bytes(b"processed thumbnail")

        return {
            "video": str(video_path),
            "thumbnail": str(thumbnail_path),
        }

    storage.download_file.side_effect = fake_download
    processor.process.side_effect = fake_process

    result = process_media.run("job-123")

    assert result["job_id"] == "job-123"
    assert result["status"] == "completed"
    assert "video" in result["output"]
    assert "thumbnail" in result["output"]

    processor.process.assert_called_once()

    storage.download_file.assert_called_once()
    assert storage.upload_file.call_count == 2

    job_store.update_status.assert_called_with(
        "job-123",
        "processing",
    )

    job_store.update_job.assert_called_once()

    update_call = job_store.update_job.call_args

    assert update_call.args[0] == "job-123"
    assert update_call.kwargs["status"] == "completed"
    assert update_call.kwargs["output"] == result["output"]


@patch("app.tasks.media_tasks.S3Storage")
@patch("app.tasks.media_tasks.JobStore")
def test_job_not_found(
    mock_job_store,
    mock_storage,
):
    job_store = mock_job_store.return_value

    job_store.get_job.return_value = None

    with pytest.raises(
        ValueError,
        match="Job not found",
    ):
        process_media.run("job-123")

    job_store.update_status.assert_not_called()
    job_store.update_job.assert_not_called()

    mock_storage.assert_called_once_with()


@patch("app.tasks.media_tasks.S3Storage")
@patch("app.tasks.media_tasks.JobStore")
def test_unsupported_media_marks_job_failed(
    mock_job_store,
    mock_storage,
):
    job_store = mock_job_store.return_value

    job_store.get_job.return_value = make_job(
        "document.pdf",
        "inputs/document.pdf",
    )

    with pytest.raises(
        ValueError,
        match="Unsupported media type",
    ):
        process_media.run("job-123")

    job_store.update_status.assert_called_with(
        "job-123",
        "processing",
    )

    job_store.update_job.assert_called_once()

    update_call = job_store.update_job.call_args

    assert update_call.args[0] == "job-123"
    assert update_call.kwargs["status"] == "failed"
    assert "Unsupported media type" in update_call.kwargs["error"]


def test_process_media_task_uses_consolidated_task():
    assert (
        process_media.name
        == "app.tasks.media_tasks.process_media"
    )