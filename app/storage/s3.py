import os

import boto3
from botocore.exceptions import ClientError


class S3Storage:
    def __init__(self, client=None):
        self.bucket_name = os.getenv("S3_BUCKET_NAME")
        self.region = os.getenv("AWS_REGION")

        if not self.bucket_name:
            raise ValueError("S3_BUCKET_NAME is not configured")

        self.client = client or boto3.client(
            "s3",
            region_name=self.region,
        )

    def upload_file(self, file_path: str, object_name: str) -> None:
        try:
            self.client.upload_file(
                file_path,
                self.bucket_name,
                object_name,
            )
        except ClientError as exc:
            raise RuntimeError("S3 upload failed") from exc

    def download_file(self, object_name: str, file_path: str) -> None:
        try:
            self.client.download_file(
                self.bucket_name,
                object_name,
                file_path,
            )
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")

            if error_code in {"404", "NoSuchKey", "NotFound"}:
                raise FileNotFoundError(
                    f"S3 object not found: {object_name}"
                ) from exc

            raise RuntimeError("S3 download failed") from exc