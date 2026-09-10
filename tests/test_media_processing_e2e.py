import pytest
from pathlib import Path

from PIL import Image


class FakeJobStore:
    def __init__(self):
        self.jobs = {}

    def create_job(
        self,
        job_id,
        filename,
        operation,
        object_key,
        status="pending",
    ):
        job = {
            "job_id": job_id,
            "status": status,
            "filename": filename,
            "operation": operation,
            "object_key": object_key,
            "error": None,
            "output": None,
        }

        self.jobs[job_id] = job
        return job

    def get_job(self, job_id):
        return self.jobs.get(job_id)

    def update_status(self, job_id, status):
        return self.update_job(
            job_id,
            status=status,
        )

    def update_job(
        self,
        job_id,
        status=None,
        output=None,
        error=None,
    ):
        job = self.jobs[job_id]

        if status is not None:
            job["status"] = status

        if output is not None:
            job["output"] = output

        if error is not None:
            job["error"] = error

        return job


class FakeS3Storage:
    def __init__(self):
        self.objects = {}
        self.uploaded_objects = []

    def upload_file(self, file_path, object_name):
        self.objects[object_name] = Path(file_path).read_bytes()
        self.uploaded_objects.append(object_name)

    def download_file(self, object_name, file_path):
        if object_name not in self.objects:
            raise FileNotFoundError(
                f"S3 object not found: {object_name}"
            )

        Path(file_path).write_bytes(
            self.objects[object_name]
        )

    def object_exists(self, object_name):
        return object_name in self.objects


@pytest.fixture
def fake_job_store():
    return FakeJobStore()


@pytest.fixture
def fake_s3():
    return FakeS3Storage()


@pytest.fixture
def image_file(tmp_path):
    image_path = tmp_path / "sample.png"

    image = Image.new(
        "RGB",
        (100, 100),
        "blue",
    )

    image.save(
        image_path,
        format="PNG",
    )

    return image_path


@pytest.fixture
def corrupt_image_file(tmp_path):
    image_path = tmp_path / "corrupt.png"

    image_path.write_bytes(
        b"this is not a valid image"
    )

    return image_path