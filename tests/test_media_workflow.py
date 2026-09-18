from pathlib import Path
from unittest.mock import Mock

import pytest

from app.storage.media_workflow import S3MediaWorkflow


def test_original_key():
    key = S3MediaWorkflow.original_key(
        "job123",
        "video.mp4",
    )

    assert key == "input/job123/original/video.mp4"


def test_processed_key():
    key = S3MediaWorkflow.processed_key(
        "job123",
        "video.mp4",
    )

    assert key == "output/job123/processed/video.mp4"


def test_thumbnail_key():
    key = S3MediaWorkflow.thumbnail_key(
        "job123",
        "thumbnail.jpg",
    )

    assert key == "output/job123/thumbnail/thumbnail.jpg"


def test_filename_path_is_sanitized():
    key = S3MediaWorkflow.original_key(
        "job123",
        "C:\\uploads\\video.mp4",
    )

    assert key == "input/job123/original/video.mp4"


def test_retrieve_input(tmp_path):
    storage = Mock()
    workflow = S3MediaWorkflow(storage=storage)

    storage.download_file.side_effect = lambda object_name, file_path: Path(
        file_path
    ).write_bytes(b"test media")

    file_path = workflow.retrieve_input(
        "job123",
        "video.mp4",
    )

    try:
        storage.download_file.assert_called_once()

        object_name, downloaded_path = (
            storage.download_file.call_args.args
        )

        assert object_name == "input/job123/original/video.mp4"
        assert downloaded_path == file_path
        assert Path(file_path).exists()
        assert Path(file_path).read_bytes() == b"test media"
    finally:
        workflow.cleanup(file_path)


def test_retrieve_input_cleans_up_when_download_fails():
    storage = Mock()
    storage.download_file.side_effect = RuntimeError(
        "S3 download failed"
    )

    workflow = S3MediaWorkflow(storage=storage)

    with pytest.raises(RuntimeError, match="S3 download failed"):
        workflow.retrieve_input(
            "job123",
            "video.mp4",
        )


def test_upload_processed(tmp_path):
    storage = Mock()
    workflow = S3MediaWorkflow(storage=storage)

    file_path = tmp_path / "optimized.mp4"
    file_path.write_bytes(b"processed media")

    object_name = workflow.upload_processed(
        "job123",
        str(file_path),
    )

    storage.upload_file.assert_called_once_with(
        str(file_path),
        "output/job123/processed/optimized.mp4",
    )

    assert object_name == (
        "output/job123/processed/optimized.mp4"
    )


def test_upload_thumbnail(tmp_path):
    storage = Mock()
    workflow = S3MediaWorkflow(storage=storage)

    file_path = tmp_path / "thumbnail.jpg"
    file_path.write_bytes(b"thumbnail")

    object_name = workflow.upload_thumbnail(
        "job123",
        str(file_path),
    )

    storage.upload_file.assert_called_once_with(
        str(file_path),
        "output/job123/thumbnail/thumbnail.jpg",
    )

    assert object_name == (
        "output/job123/thumbnail/thumbnail.jpg"
    )


def test_upload_processed_failure(tmp_path):
    storage = Mock()
    storage.upload_file.side_effect = RuntimeError(
        "S3 upload failed"
    )

    workflow = S3MediaWorkflow(storage=storage)

    file_path = tmp_path / "optimized.mp4"
    file_path.write_bytes(b"processed media")

    with pytest.raises(RuntimeError, match="S3 upload failed"):
        workflow.upload_processed(
            "job123",
            str(file_path),
        )


def test_upload_thumbnail_failure(tmp_path):
    storage = Mock()
    storage.upload_file.side_effect = RuntimeError(
        "S3 upload failed"
    )

    workflow = S3MediaWorkflow(storage=storage)

    file_path = tmp_path / "thumbnail.jpg"
    file_path.write_bytes(b"thumbnail")

    with pytest.raises(RuntimeError, match="S3 upload failed"):
        workflow.upload_thumbnail(
            "job123",
            str(file_path),
        )


def test_cleanup(tmp_path):
    storage = Mock()
    workflow = S3MediaWorkflow(storage=storage)

    file1 = tmp_path / "input.mp4"
    file2 = tmp_path / "thumbnail.jpg"

    file1.write_bytes(b"input")
    file2.write_bytes(b"thumbnail")

    assert file1.exists()
    assert file2.exists()

    workflow.cleanup(
        str(file1),
        str(file2),
    )

    assert not file1.exists()
    assert not file2.exists()