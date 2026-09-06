import os

from app.core import config
import boto3
from botocore.config import Config
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
            endpoint_url=os.getenv("S3_ENDPOINT_URL"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
            ),
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

    def object_exists(self, object_name: str) -> bool:
        try:
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=object_name,
            )
            return True
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")

            if error_code in {"404", "NoSuchKey", "NotFound"}:
                return False

            raise RuntimeError(
                "S3 object existence check failed"
            ) from exc

    def generate_presigned_upload_url(
        self,
        object_name: str,
        expiration: int = 3600,
    ) -> str:
        """Generate a presigned URL for uploading an object to S3."""
        try:
            return self.client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": object_name,
                },
                ExpiresIn=expiration,
            )
        except ClientError as exc:
            raise RuntimeError(
                "Failed to generate presigned upload URL"
            ) from exc