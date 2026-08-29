import pytest
from botocore.exceptions import ClientError

from app.storage.s3 import S3Storage


def test_missing_bucket_configuration(monkeypatch):
    monkeypatch.delenv("S3_BUCKET_NAME", raising=False)

    with pytest.raises(ValueError, match="S3_BUCKET_NAME is not configured"):
        S3Storage()


def test_upload_success(monkeypatch, tmp_path):
    monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("AWS_REGION", "ap-south-1")

    storage = S3Storage()

    upload_file = tmp_path / "sample.txt"
    upload_file.write_text("test data")

    storage.client.upload_file = lambda *args: None

    storage.upload_file(str(upload_file), "sample.txt")


def test_upload_failure(monkeypatch, tmp_path):
    monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("AWS_REGION", "ap-south-1")

    storage = S3Storage()

    upload_file = tmp_path / "sample.txt"
    upload_file.write_text("test data")

    def failed_upload(*args):
        raise ClientError(
            {
                "Error": {
                    "Code": "500",
                    "Message": "Upload failed",
                }
            },
            "UploadFile",
        )

    storage.client.upload_file = failed_upload

    with pytest.raises(RuntimeError, match="S3 upload failed"):
        storage.upload_file(str(upload_file), "sample.txt")


def test_download_success(monkeypatch, tmp_path):
    monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("AWS_REGION", "ap-south-1")

    storage = S3Storage()

    download_file = tmp_path / "downloaded.txt"

    storage.client.download_file = lambda *args: download_file.write_text(
        "downloaded data"
    )

    storage.download_file("sample.txt", str(download_file))

    assert download_file.read_text() == "downloaded data"


def test_download_failure(monkeypatch, tmp_path):
    monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("AWS_REGION", "ap-south-1")

    storage = S3Storage()

    download_file = tmp_path / "downloaded.txt"

    def failed_download(*args):
        raise ClientError(
            {
                "Error": {
                    "Code": "500",
                    "Message": "Download failed",
                }
            },
            "DownloadFile",
        )

    storage.client.download_file = failed_download

    with pytest.raises(RuntimeError, match="S3 download failed"):
        storage.download_file("sample.txt", str(download_file))


def test_object_not_found(monkeypatch, tmp_path):
    monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("AWS_REGION", "ap-south-1")

    storage = S3Storage()

    download_file = tmp_path / "downloaded.txt"

    def object_not_found(*args):
        raise ClientError(
            {
                "Error": {
                    "Code": "NoSuchKey",
                    "Message": "The specified key does not exist.",
                }
            },
            "DownloadFile",
        )

    storage.client.download_file = object_not_found

    with pytest.raises(FileNotFoundError, match="S3 object not found"):
        storage.download_file("missing.txt", str(download_file))