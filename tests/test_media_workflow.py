import io
from pathlib import Path

import pytest
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
        return self.update_job(job_id, status=status)

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

        Path(file_path).write_bytes(self.objects[object_name])

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
    image.save(image_path, format="PNG")

    return image_path


@pytest.fixture
def corrupt_image_file(tmp_path):
    image_path = tmp_path / "corrupt.png"
    image_path.write_bytes(b"this is not a valid image")

    return image_path


def test_create_media_job(fake_job_store):
    job = fake_job_store.create_job(
        job_id="job-001",
        filename="sample.png",
        operation="resize",
        object_key="uploads/sample.png",
    )

    assert job["job_id"] == "job-001"
    assert job["status"] == "pending"
    assert job["filename"] == "sample.png"
    assert job["operation"] == "resize"
    assert job["object_key"] == "uploads/sample.png"


def test_job_status_workflow(fake_job_store):
    fake_job_store.create_job(
        job_id="job-002",
        filename="sample.png",
        operation="resize",
        object_key="uploads/sample.png",
    )

    assert fake_job_store.get_job("job-002")["status"] == "pending"

    fake_job_store.update_status("job-002", "processing")
    assert fake_job_store.get_job("job-002")["status"] == "processing"

    fake_job_store.update_status("job-002", "completed")
    assert fake_job_store.get_job("job-002")["status"] == "completed"


def test_image_upload_and_download(fake_s3, image_file, tmp_path):
    object_key = "uploads/sample.png"

    fake_s3.upload_file(image_file, object_key)

    assert fake_s3.object_exists(object_key)
    assert object_key in fake_s3.uploaded_objects

    downloaded_file = tmp_path / "downloaded.png"
    fake_s3.download_file(object_key, downloaded_file)

    assert downloaded_file.exists()
    assert downloaded_file.read_bytes() == image_file.read_bytes()


def test_image_processing_workflow(
    fake_job_store,
    fake_s3,
    image_file,
    tmp_path,
):
    job_id = "job-image-001"
    input_key = "uploads/sample.png"
    output_key = "outputs/job-image-001.png"

    fake_s3.upload_file(image_file, input_key)

    fake_job_store.create_job(
        job_id=job_id,
        filename="sample.png",
        operation="resize",
        object_key=input_key,
    )

    fake_job_store.update_status(job_id, "processing")

    downloaded_file = tmp_path / "input.png"
    fake_s3.download_file(input_key, downloaded_file)

    with Image.open(downloaded_file) as image:
        resized = image.resize((50, 50))
        output_file = tmp_path / "output.png"
        resized.save(output_file, format="PNG")

    fake_s3.upload_file(output_file, output_key)

    fake_job_store.update_job(
        job_id,
        status="completed",
        output=output_key,
    )

    job = fake_job_store.get_job(job_id)

    assert job["status"] == "completed"
    assert job["output"] == output_key
    assert fake_s3.object_exists(output_key)

    with Image.open(output_file) as output_image:
        assert output_image.size == (50, 50)


def test_corrupt_image_fails(
    fake_job_store,
    corrupt_image_file,
):
    job_id = "job-corrupt-001"
    input_key = "uploads/corrupt.png"

    fake_job_store.create_job(
        job_id=job_id,
        filename="corrupt.png",
        operation="resize",
        object_key=input_key,
    )

    fake_job_store.update_status(job_id, "processing")

    with pytest.raises(Exception):
        with Image.open(corrupt_image_file) as image:
            image.verify()

    fake_job_store.update_job(
        job_id,
        status="failed",
        error="Invalid or corrupted image",
    )

    job = fake_job_store.get_job(job_id)

    assert job["status"] == "failed"
    assert job["error"] == "Invalid or corrupted image"


def test_missing_s3_object_fails(fake_job_store, fake_s3, tmp_path):
    job_id = "job-missing-001"
    input_key = "uploads/missing.png"

    fake_job_store.create_job(
        job_id=job_id,
        filename="missing.png",
        operation="resize",
        object_key=input_key,
    )

    fake_job_store.update_status(job_id, "processing")

    downloaded_file = tmp_path / "missing.png"

    with pytest.raises(FileNotFoundError):
        fake_s3.download_file(input_key, downloaded_file)

    fake_job_store.update_job(
        job_id,
        status="failed",
        error=f"S3 object not found: {input_key}",
    )

    job = fake_job_store.get_job(job_id)

    assert job["status"] == "failed"
    assert input_key in job["error"]


def test_multiple_jobs_are_independent(fake_job_store):
    fake_job_store.create_job(
        job_id="job-101",
        filename="one.png",
        operation="resize",
        object_key="uploads/one.png",
    )

    fake_job_store.create_job(
        job_id="job-102",
        filename="two.png",
        operation="compress",
        object_key="uploads/two.png",
    )

    fake_job_store.update_status("job-101", "completed")
    fake_job_store.update_status("job-102", "failed")

    job_one = fake_job_store.get_job("job-101")
    job_two = fake_job_store.get_job("job-102")

    assert job_one["status"] == "completed"
    assert job_two["status"] == "failed"
    assert job_one["job_id"] != job_two["job_id"]


def test_failed_job_stores_error(fake_job_store):
    fake_job_store.create_job(
        job_id="job-error-001",
        filename="sample.png",
        operation="resize",
        object_key="uploads/sample.png",
    )

    fake_job_store.update_job(
        "job-error-001",
        status="failed",
        error="Media processing failed",
    )

    job = fake_job_store.get_job("job-error-001")

    assert job["status"] == "failed"
    assert job["error"] == "Media processing failed"

from app.worker.tasks import process_media


def test_process_media_task_returns_completed():
    result = process_media.run("job-celery-001")

    assert result["job_id"] == "job-celery-001"
    assert result["status"] == "COMPLETED"


def test_process_media_task_has_retry_configuration():
    assert process_media.autoretry_for == (Exception,)
    assert process_media.max_retries == 3


def test_retry_configuration_allows_transient_failure():
    attempts = {"count": 0}

    @process_media.app.task(
        bind=True,
        autoretry_for=(Exception,),
        retry_backoff=False,
        retry_kwargs={"max_retries": 3},
    )
    def flaky_task(self):
        attempts["count"] += 1

        if attempts["count"] < 2:
            raise RuntimeError("Temporary processing failure")

        return {
            "status": "COMPLETED",
            "attempts": attempts["count"],
        }

    result = flaky_task.apply()

    assert result.successful()
    assert result.result["status"] == "COMPLETED"
    assert result.result["attempts"] == 2


def test_retry_configuration_stops_after_max_retries():
    attempts = {"count": 0}

    @process_media.app.task(
        bind=True,
        autoretry_for=(Exception,),
        retry_backoff=False,
        retry_kwargs={"max_retries": 2},
    )
    def failing_task(self):
        attempts["count"] += 1
        raise RuntimeError("Permanent processing failure")

    result = failing_task.apply()

    assert result.failed()
    assert attempts["count"] == 3