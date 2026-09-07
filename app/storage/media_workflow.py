import os
import tempfile
from pathlib import Path

from app.storage.s3 import S3Storage


class S3MediaWorkflow:
    """Handles S3 object naming and media workflow operations."""

    def __init__(self, storage=None):
        self.storage = storage or S3Storage()

    @staticmethod
    def original_key(job_id: str, filename: str) -> str:
        return f"input/{job_id}/original/{Path(filename).name}"

    @staticmethod
    def processed_key(job_id: str, filename: str) -> str:
        return f"output/{job_id}/processed/{Path(filename).name}"

    @staticmethod
    def thumbnail_key(job_id: str, filename: str) -> str:
        return f"output/{job_id}/thumbnail/{Path(filename).name}"

    def retrieve_input(self, job_id: str, filename: str) -> str:
        """Download the original media from S3 to a temporary local file."""
        object_name = self.original_key(job_id, filename)

        suffix = Path(filename).suffix
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        )
        temp_file.close()

        try:
            self.storage.download_file(
                object_name,
                temp_file.name,
            )
            return temp_file.name
        except Exception:
            self._cleanup(temp_file.name)
            raise

    def upload_processed(
        self,
        job_id: str,
        file_path: str,
        filename: str | None = None,
    ) -> str:
        """Upload a processed media file to S3."""
        filename = filename or Path(file_path).name
        object_name = self.processed_key(job_id, filename)

        self.storage.upload_file(file_path, object_name)
        return object_name

    def upload_thumbnail(
        self,
        job_id: str,
        file_path: str,
        filename: str | None = None,
    ) -> str:
        """Upload a video thumbnail to S3."""
        filename = filename or Path(file_path).name
        object_name = self.thumbnail_key(job_id, filename)

        self.storage.upload_file(file_path, object_name)
        return object_name

    def cleanup(self, *file_paths: str) -> None:
        """Remove local temporary files."""
        for file_path in file_paths:
            self._cleanup(file_path)

    @staticmethod
    def _cleanup(file_path: str) -> None:
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            pass