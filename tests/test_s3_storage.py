import pytest
from unittest.mock import Mock
from botocore.exceptions import ClientError

from app.storage.s3 import S3Storage


def create_client_error(error_code):
    return ClientError(
        {
            "Error": {
                "Code": error_code,
                "Message": "Test error",
            }
        },
        "TestOperation",
    )


def test_missing_bucket_configuration(monkeypatch):
    monkeypatch.delenv("S3_BUCKET_NAME", raising=False)

    with pytest.raises(ValueError, match="S3_BUCKET_NAME is not configured"):
        S3Storage(client=Mock())


def test_upload_success(monkeypatch):
    monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")

    client = Mock()
    storage = S3Storage(client=client)

    storage.upload_file("test.mp4", "media/test.mp4")

    client.upload_file.assert_called_once_with(
        "test.mp4",
        "test-bucket",
        "media/test.mp4",
    )


def test_upload_failure(monkeypatch):
    monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")

    client = Mock()
    client.upload_file.side_effect = create_client_error("AccessDenied")

    storage = S3Storage(client=client)

    with pytest.raises(RuntimeError, match="S3 upload failed"):
        storage.upload_file("test.mp4", "media/test.mp4")


def test_download_success(monkeypatch):
    monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")

    client = Mock()
    storage = S3Storage(client=client)

    storage.download_file(
        "media/test.mp4",
        "downloaded.mp4",
    )

    client.download_file.assert_called_once_with(
        "test-bucket",
        "media/test.mp4",
        "downloaded.mp4",
    )


def test_download_failure(monkeypatch):
    monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")

    client = Mock()
    client.download_file.side_effect = create_client_error("AccessDenied")

    storage = S3Storage(client=client)

    with pytest.raises(RuntimeError, match="S3 download failed"):
        storage.download_file(
            "media/test.mp4",
            "downloaded.mp4",
        )


def test_object_not_found(monkeypatch):
    monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")

    client = Mock()
    client.download_file.side_effect = create_client_error("404")

    storage = S3Storage(client=client)

    with pytest.raises(
        FileNotFoundError,
        match="S3 object not found",
    ):
        storage.download_file(
            "missing.mp4",
            "downloaded.mp4",
        )


def test_object_exists(monkeypatch):
    monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")

    client = Mock()
    client.head_object.return_value = {}

    storage = S3Storage(client=client)

    result = storage.object_exists("media/test.mp4")

    assert result is True

    client.head_object.assert_called_once_with(
        Bucket="test-bucket",
        Key="media/test.mp4",
    )


def test_object_does_not_exist(monkeypatch):
    monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")

    client = Mock()
    client.head_object.side_effect = create_client_error("404")

    storage = S3Storage(client=client)

    result = storage.object_exists("media/missing.mp4")

    assert result is False


def test_object_exists_other_error(monkeypatch):
    monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")

    client = Mock()
    client.head_object.side_effect = create_client_error("AccessDenied")

    storage = S3Storage(client=client)

    with pytest.raises(
        RuntimeError,
        match="S3 object existence check failed",
    ):
        storage.object_exists("media/test.mp4")