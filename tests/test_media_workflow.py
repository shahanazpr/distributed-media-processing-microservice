import io
from pathlib import Path

import pytest
from PIL import Image

from app.tasks.media_tasks import process_media


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

    def upload_file(
        self,
        file_path,
        object_name,
    ):
        self.objects[object_name] = (
            Path(file_path).read_bytes()
        )

        self.uploaded_objects.append(
            object_name
        )

    def download_file(
        self,
        object_name,
        file_path,
    ):
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


# ---------------------------------------------------------
# BASIC JOB WORKFLOW TESTS
# ---------------------------------------------------------


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

    assert (
        fake_job_store
        .get_job("job-002")["status"]
        == "pending"
    )

    fake_job_store.update_status(
        "job-002",
        "processing",
    )

    assert (
        fake_job_store
        .get_job("job-002")["status"]
        == "processing"
    )

    fake_job_store.update_status(
        "job-002",
        "completed",
    )

    assert (
        fake_job_store
        .get_job("job-002")["status"]
        == "completed"
    )


def test_image_upload_and_download(
    fake_s3,
    image_file,
    tmp_path,
):
    object_key = "uploads/sample.png"

    fake_s3.upload_file(
        image_file,
        object_key,
    )

    assert fake_s3.object_exists(
        object_key
    )

    assert (
        object_key
        in fake_s3.uploaded_objects
    )

    downloaded_file = (
        tmp_path / "downloaded.png"
    )

    fake_s3.download_file(
        object_key,
        downloaded_file,
    )

    assert downloaded_file.exists()

    assert (
        downloaded_file.read_bytes()
        == image_file.read_bytes()
    )


# ---------------------------------------------------------
# IMAGE PROCESSING TESTS
# ---------------------------------------------------------


def test_image_processing_workflow(
    fake_job_store,
    fake_s3,
    image_file,
    tmp_path,
):
    job_id = "job-image-001"

    input_key = "uploads/sample.png"
    output_key = (
        "outputs/job-image-001.png"
    )

    fake_s3.upload_file(
        image_file,
        input_key,
    )

    fake_job_store.create_job(
        job_id=job_id,
        filename="sample.png",
        operation="resize",
        object_key=input_key,
    )

    fake_job_store.update_status(
        job_id,
        "processing",
    )

    downloaded_file = (
        tmp_path / "input.png"
    )

    fake_s3.download_file(
        input_key,
        downloaded_file,
    )

    with Image.open(
        downloaded_file
    ) as image:
        resized = image.resize(
            (50, 50)
        )

        output_file = (
            tmp_path / "output.png"
        )

        resized.save(
            output_file,
            format="PNG",
        )

    fake_s3.upload_file(
        output_file,
        output_key,
    )

    fake_job_store.update_job(
        job_id,
        status="completed",
        output=output_key,
    )

    job = fake_job_store.get_job(
        job_id
    )

    assert job["status"] == "completed"
    assert job["output"] == output_key

    assert fake_s3.object_exists(
        output_key
    )

    with Image.open(
        output_file
    ) as output_image:
        assert output_image.size == (
            50,
            50,
        )


def test_corrupt_image_fails(
    fake_job_store,
    corrupt_image_file,
):
    job_id = "job-corrupt-001"

    input_key = (
        "uploads/corrupt.png"
    )

    fake_job_store.create_job(
        job_id=job_id,
        filename="corrupt.png",
        operation="resize",
        object_key=input_key,
    )

    fake_job_store.update_status(
        job_id,
        "processing",
    )

    with pytest.raises(Exception):
        with Image.open(
            corrupt_image_file
        ) as image:
            image.verify()

    fake_job_store.update_job(
        job_id,
        status="failed",
        error="Invalid or corrupted image",
    )

    job = fake_job_store.get_job(
        job_id
    )

    assert job["status"] == "failed"

    assert (
        job["error"]
        == "Invalid or corrupted image"
    )


# ---------------------------------------------------------
# S3 FAILURE TEST
# ---------------------------------------------------------


def test_missing_s3_object_fails(
    fake_job_store,
    fake_s3,
    tmp_path,
):
    job_id = "job-missing-001"

    input_key = (
        "uploads/missing.png"
    )

    fake_job_store.create_job(
        job_id=job_id,
        filename="missing.png",
        operation="resize",
        object_key=input_key,
    )

    fake_job_store.update_status(
        job_id,
        "processing",
    )

    downloaded_file = (
        tmp_path / "missing.png"
    )

    with pytest.raises(
        FileNotFoundError
    ):
        fake_s3.download_file(
            input_key,
            downloaded_file,
        )

    fake_job_store.update_job(
        job_id,
        status="failed",
        error=(
            f"S3 object not found: "
            f"{input_key}"
        ),
    )

    job = fake_job_store.get_job(
        job_id
    )

    assert job["status"] == "failed"

    assert input_key in job["error"]


# ---------------------------------------------------------
# MULTIPLE JOBS
# ---------------------------------------------------------


def test_multiple_jobs_are_independent(
    fake_job_store,
):
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

    fake_job_store.update_status(
        "job-101",
        "completed",
    )

    fake_job_store.update_status(
        "job-102",
        "failed",
    )

    job_one = fake_job_store.get_job(
        "job-101"
    )

    job_two = fake_job_store.get_job(
        "job-102"
    )

    assert job_one["status"] == "completed"
    assert job_two["status"] == "failed"

    assert (
        job_one["job_id"]
        != job_two["job_id"]
    )


def test_failed_job_stores_error(
    fake_job_store,
):
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

    job = fake_job_store.get_job(
        "job-error-001"
    )

    assert job["status"] == "failed"

    assert (
        job["error"]
        == "Media processing failed"
    )


# ---------------------------------------------------------
# REAL IMAGE MEDIA TASK
# ---------------------------------------------------------


def test_real_image_media_task_workflow(
    monkeypatch,
):
    from app.tasks import media_tasks

    job_id = "image-e2e-001"

    jobs = {
        job_id: {
            "job_id": job_id,
            "filename": "input.png",
            "object_key": (
                "input/image-e2e-001/"
                "original/input.png"
            ),
            "status": "pending",
        }
    }

    uploaded = {}
    statuses = []

    class FakeJobStore:
        def get_job(
            self,
            requested_job_id,
        ):
            return jobs.get(
                requested_job_id
            )

        def update_status(
            self,
            requested_job_id,
            status,
        ):
            jobs[requested_job_id][
                "status"
            ] = status

            statuses.append(status)

        def update_job(
            self,
            job_id,
            status,
            output=None,
            error=None,
        ):
            jobs[job_id]["status"] = status

            if output is not None:
                jobs[job_id]["output"] = (
                    output
                )

            if error is not None:
                jobs[job_id]["error"] = (
                    error
                )

    class FakeS3Storage:
        def download_file(
            self,
            object_name,
            file_path,
        ):
            image = Image.new(
                "RGB",
                (100, 100),
                "blue",
            )

            image.save(
                file_path,
                format="PNG",
            )

        def upload_file(
            self,
            file_path,
            object_name,
        ):
            uploaded[object_name] = (
                Path(file_path).read_bytes()
            )

    monkeypatch.setattr(
        media_tasks,
        "JobStore",
        FakeJobStore,
    )

    monkeypatch.setattr(
        media_tasks,
        "S3Storage",
        FakeS3Storage,
    )

    result = process_media.apply(
        args=[job_id]
    )

    assert result.successful()

    assert (
        result.result["job_id"]
        == job_id
    )

    assert (
        result.result["status"]
        == "completed"
    )

    assert statuses == [
        "processing"
    ]

    assert (
        jobs[job_id]["status"]
        == "completed"
    )

    output_key = (
        "outputs/image-e2e-001/"
        "input_processed.jpg"
    )

    assert output_key in uploaded

    assert (
        jobs[job_id]["output"][
            "object_key"
        ]
        == output_key
    )


# ---------------------------------------------------------
# REAL VIDEO MEDIA TASK
# ---------------------------------------------------------


def test_real_video_media_task_workflow(
    monkeypatch,
):
    from app.tasks import media_tasks

    job_id = "video-e2e-001"

    jobs = {
        job_id: {
            "job_id": job_id,
            "filename": "input.mp4",
            "object_key": (
                "input/video-e2e-001/"
                "original/input.mp4"
            ),
            "status": "pending",
        }
    }

    uploaded = {}
    statuses = []

    class FakeJobStore:
        def get_job(
            self,
            requested_job_id,
        ):
            return jobs.get(
                requested_job_id
            )

        def update_status(
            self,
            requested_job_id,
            status,
        ):
            jobs[requested_job_id][
                "status"
            ] = status

            statuses.append(status)

        def update_job(
            self,
            job_id,
            status,
            output=None,
            error=None,
        ):
            jobs[job_id]["status"] = status

            if output is not None:
                jobs[job_id]["output"] = (
                    output
                )

            if error is not None:
                jobs[job_id]["error"] = (
                    error
                )

    class FakeS3Storage:
        def download_file(
            self,
            object_name,
            file_path,
        ):
            Path(file_path).write_bytes(
                b"fake video input"
            )

        def upload_file(
            self,
            file_path,
            object_name,
        ):
            uploaded[object_name] = (
                Path(file_path).read_bytes()
            )

    class FakeFFmpegProcessor:
        def process(
            self,
            input_path,
            output_dir,
        ):
            output_dir = Path(
                output_dir
            )

            video_path = (
                output_dir
                / "optimized.mp4"
            )

            thumbnail_path = (
                output_dir
                / "thumbnail.jpg"
            )

            video_path.write_bytes(
                b"processed video"
            )

            thumbnail_path.write_bytes(
                b"processed thumbnail"
            )

            return {
                "video": str(
                    video_path
                ),
                "thumbnail": str(
                    thumbnail_path
                ),
            }

    monkeypatch.setattr(
        media_tasks,
        "JobStore",
        FakeJobStore,
    )

    monkeypatch.setattr(
        media_tasks,
        "S3Storage",
        FakeS3Storage,
    )

    monkeypatch.setattr(
        media_tasks,
        "FFmpegProcessor",
        FakeFFmpegProcessor,
    )

    result = process_media.apply(
        args=[job_id]
    )

    assert result.successful()

    assert (
        result.result["job_id"]
        == job_id
    )

    assert (
        result.result["status"]
        == "completed"
    )

    assert statuses == [
        "processing"
    ]

    assert (
        jobs[job_id]["status"]
        == "completed"
    )

    assert (
        "outputs/video-e2e-001/"
        "optimized.mp4"
        in uploaded
    )

    assert (
        "outputs/video-e2e-001/"
        "thumbnail.jpg"
        in uploaded
    )

    output = jobs[job_id]["output"]

    assert (
        output["video"]["object_key"]
        == (
            "outputs/video-e2e-001/"
            "optimized.mp4"
        )
    )

    assert (
        output["thumbnail"]["object_key"]
        == (
            "outputs/video-e2e-001/"
            "thumbnail.jpg"
        )
    )


# ---------------------------------------------------------
# REAL TASK - MISSING S3 OBJECT
# ---------------------------------------------------------


def test_real_media_task_missing_s3_object_fails(
    monkeypatch,
):
    from app.tasks import media_tasks

    job_id = "missing-s3-001"

    jobs = {
        job_id: {
            "job_id": job_id,
            "filename": "input.png",
            "object_key": "missing/input.png",
            "status": "pending",
        }
    }

    class FakeJobStore:
        def get_job(
            self,
            requested_job_id,
        ):
            return jobs.get(
                requested_job_id
            )

        def update_status(
            self,
            requested_job_id,
            status,
        ):
            jobs[requested_job_id][
                "status"
            ] = status

        def update_job(
            self,
            job_id,
            status,
            output=None,
            error=None,
        ):
            jobs[job_id]["status"] = status

            if error is not None:
                jobs[job_id]["error"] = (
                    error
                )

    class FakeS3Storage:
        def download_file(
            self,
            object_name,
            file_path,
        ):
            raise FileNotFoundError(
                f"S3 object not found: "
                f"{object_name}"
            )

    monkeypatch.setattr(
        media_tasks,
        "JobStore",
        FakeJobStore,
    )

    monkeypatch.setattr(
        media_tasks,
        "S3Storage",
        FakeS3Storage,
    )

    result = process_media.apply(
        args=[job_id]
    )

    assert result.failed()

    assert (
        jobs[job_id]["status"]
        == "failed"
    )

    assert "error" in jobs[job_id]

    assert (
        "S3 object not found"
        in jobs[job_id]["error"]
    )


# ---------------------------------------------------------
# REAL TASK - PROCESSING FAILURE
# ---------------------------------------------------------


def test_real_media_task_processing_failure(
    monkeypatch,
):
    from app.tasks import media_tasks

    job_id = (
        "processing-failure-001"
    )

    jobs = {
        job_id: {
            "job_id": job_id,
            "filename": "input.mp4",
            "object_key": (
                "input/failure/input.mp4"
            ),
            "status": "pending",
        }
    }

    class FakeJobStore:
        def get_job(
            self,
            requested_job_id,
        ):
            return jobs.get(
                requested_job_id
            )

        def update_status(
            self,
            requested_job_id,
            status,
        ):
            jobs[requested_job_id][
                "status"
            ] = status

        def update_job(
            self,
            job_id,
            status,
            output=None,
            error=None,
        ):
            jobs[job_id]["status"] = status

            if error is not None:
                jobs[job_id]["error"] = (
                    error
                )

    class FakeS3Storage:
        def download_file(
            self,
            object_name,
            file_path,
        ):
            Path(file_path).write_bytes(
                b"fake video"
            )

        def upload_file(
            self,
            file_path,
            object_name,
        ):
            raise RuntimeError(
                "S3 upload failed"
            )

    class FakeFFmpegProcessor:
        def process(
            self,
            input_path,
            output_dir,
        ):
            output_dir = Path(
                output_dir
            )

            video_path = (
                output_dir
                / "optimized.mp4"
            )

            thumbnail_path = (
                output_dir
                / "thumbnail.jpg"
            )

            video_path.write_bytes(
                b"processed video"
            )

            thumbnail_path.write_bytes(
                b"processed thumbnail"
            )

            return {
                "video": str(
                    video_path
                ),
                "thumbnail": str(
                    thumbnail_path
                ),
            }

    monkeypatch.setattr(
        media_tasks,
        "JobStore",
        FakeJobStore,
    )

    monkeypatch.setattr(
        media_tasks,
        "S3Storage",
        FakeS3Storage,
    )

    monkeypatch.setattr(
        media_tasks,
        "FFmpegProcessor",
        FakeFFmpegProcessor,
    )

    result = process_media.apply(
        args=[job_id]
    )

    assert result.failed()

    assert (
        jobs[job_id]["status"]
        == "failed"
    )

    assert (
        jobs[job_id]["error"]
        == "S3 upload failed"
    )


# ---------------------------------------------------------
# REAL TASK - UNSUPPORTED MEDIA
# ---------------------------------------------------------


def test_real_media_task_unsupported_media_fails(
    monkeypatch,
):
    from app.tasks import media_tasks

    job_id = "unsupported-001"

    jobs = {
        job_id: {
            "job_id": job_id,
            "filename": "input.txt",
            "object_key": (
                "input/unsupported/"
                "input.txt"
            ),
            "status": "pending",
        }
    }

    class FakeJobStore:
        def get_job(
            self,
            requested_job_id,
        ):
            return jobs.get(
                requested_job_id
            )

        def update_status(
            self,
            requested_job_id,
            status,
        ):
            jobs[requested_job_id][
                "status"
            ] = status

        def update_job(
            self,
            job_id,
            status,
            output=None,
            error=None,
        ):
            jobs[job_id]["status"] = status

            if error is not None:
                jobs[job_id]["error"] = (
                    error
                )

    class FakeS3Storage:
        def download_file(
            self,
            object_name,
            file_path,
        ):
            Path(file_path).write_text(
                "not media"
            )

    monkeypatch.setattr(
        media_tasks,
        "JobStore",
        FakeJobStore,
    )

    monkeypatch.setattr(
        media_tasks,
        "S3Storage",
        FakeS3Storage,
    )

    result = process_media.apply(
        args=[job_id]
    )

    assert result.failed()

    assert (
        jobs[job_id]["status"]
        == "failed"
    )

    assert "error" in jobs[job_id]

    assert (
        "Unsupported media type"
        in jobs[job_id]["error"]
    )


# ---------------------------------------------------------
# CELERY RETRY TESTS
# ---------------------------------------------------------


def test_process_media_task_has_retry_configuration():
    assert process_media.autoretry_for == (
        ConnectionError,
        TimeoutError,
    )

    assert (
        process_media.max_retries
        == 3
    )

    assert (
        process_media.retry_backoff
        is True
    )


def test_retry_configuration_allows_transient_failure():
    attempts = {"count": 0}

    @process_media.app.task(
        bind=True,
        autoretry_for=(
            ConnectionError,
            TimeoutError,
        ),
        retry_backoff=False,
        retry_kwargs={
            "max_retries": 3
        },
    )
    def flaky_task(self):
        attempts["count"] += 1

        if attempts["count"] < 2:
            raise ConnectionError(
                "Temporary connection failure"
            )

        return {
            "status": "COMPLETED",
            "attempts": attempts[
                "count"
            ],
        }

    result = flaky_task.apply()

    assert result.successful()

    assert (
        result.result["status"]
        == "COMPLETED"
    )

    assert (
        result.result["attempts"]
        == 2
    )


def test_retry_configuration_stops_after_max_retries():
    attempts = {"count": 0}

    @process_media.app.task(
        bind=True,
        autoretry_for=(
            ConnectionError,
            TimeoutError,
        ),
        retry_backoff=False,
        retry_kwargs={
            "max_retries": 2
        },
    )
    def failing_task(self):
        attempts["count"] += 1

        raise ConnectionError(
            "Permanent connection failure"
        )

    result = failing_task.apply()

    assert result.failed()

    assert attempts["count"] == 3