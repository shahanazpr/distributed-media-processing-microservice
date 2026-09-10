from pathlib import Path

import pytest

from app.tasks.media_tasks import process_media


def test_process_media_image_success(tmp_path, monkeypatch):
    job_id = "test-image-job"

    job = {
        "job_id": job_id,
        "filename": "input.png",
        "operation": "resize",
        "object_key": f"uploads/{job_id}/input.png",
        "status": "pending",
    }

    events = []

    class FakeJobStore:
        jobs = {job_id: job.copy()}

        def get_job(self, requested_job_id):
            events.append(("get_job", requested_job_id))
            return self.jobs.get(requested_job_id)

        def update_status(self, requested_job_id, status):
            events.append(("update_status", status))
            self.jobs[requested_job_id]["status"] = status
            return self.jobs[requested_job_id]

        def update_job(
            self,
            requested_job_id,
            status=None,
            output=None,
            error=None,
        ):
            events.append(("update_job", status))

            if status is not None:
                self.jobs[requested_job_id]["status"] = status

            if output is not None:
                self.jobs[requested_job_id]["output"] = output

            if error is not None:
                self.jobs[requested_job_id]["error"] = error

            return self.jobs[requested_job_id]

    class FakeS3Storage:
        def download_file(self, object_name, file_path):
            events.append(("download", object_name))
            assert object_name == job["object_key"]
            Path(file_path).write_bytes(b"fake image")

        def upload_file(self, file_path, object_name):
            events.append(("upload", object_name))
            assert Path(file_path).exists()
            assert object_name.startswith(f"outputs/{job_id}/")

    class FakeImageProcessor:
        def process(self, input_path, output_path):
            events.append(("process", Path(input_path).name))
            assert Path(input_path).exists()
            Path(output_path).write_bytes(b"processed image")
            return output_path

    monkeypatch.setattr(
        "app.tasks.media_tasks.JobStore",
        FakeJobStore,
    )

    monkeypatch.setattr(
        "app.tasks.media_tasks.S3Storage",
        FakeS3Storage,
    )

    monkeypatch.setattr(
        "app.tasks.media_tasks.ImageProcessor",
        FakeImageProcessor,
    )

    result = process_media.run(job_id)

    assert result["job_id"] == job_id
    assert result["status"] == "completed"

    assert FakeJobStore.jobs[job_id]["status"] == "completed"
    assert "output" in FakeJobStore.jobs[job_id]

    event_names = [event[0] for event in events]

    assert event_names == [
        "get_job",
        "update_status",
        "download",
        "process",
        "upload",
        "update_job",
    ]

    assert events[1] == ("update_status", "processing")
    assert events[2] == ("download", job["object_key"])
    assert events[4][0] == "upload"
    assert events[5] == ("update_job", "completed")


def test_process_media_video_success(tmp_path, monkeypatch):
    job_id = "test-video-job"

    job = {
        "job_id": job_id,
        "filename": "input.mp4",
        "operation": "resize",
        "object_key": f"uploads/{job_id}/input.mp4",
        "status": "pending",
    }

    class FakeJobStore:
        jobs = {job_id: job.copy()}

        def get_job(self, requested_job_id):
            return self.jobs.get(requested_job_id)

        def update_status(self, requested_job_id, status):
            self.jobs[requested_job_id]["status"] = status
            return self.jobs[requested_job_id]

        def update_job(
            self,
            requested_job_id,
            status=None,
            output=None,
            error=None,
        ):
            if status is not None:
                self.jobs[requested_job_id]["status"] = status

            if output is not None:
                self.jobs[requested_job_id]["output"] = output

            if error is not None:
                self.jobs[requested_job_id]["error"] = error

            return self.jobs[requested_job_id]

    class FakeS3Storage:
        def download_file(self, object_name, file_path):
            Path(file_path).write_bytes(b"fake video")

        def upload_file(self, file_path, object_name):
            assert Path(file_path).exists()
            assert object_name.startswith(f"outputs/{job_id}/")

    class FakeFFmpegProcessor:
        def process(self, input_path, output_dir):
            output_dir = Path(output_dir)

            video_path = output_dir / "optimized.mp4"
            thumbnail_path = output_dir / "thumbnail.jpg"

            video_path.write_bytes(b"processed video")
            thumbnail_path.write_bytes(b"processed thumbnail")

            return {
                "video": str(video_path),
                "thumbnail": str(thumbnail_path),
            }

    monkeypatch.setattr(
        "app.tasks.media_tasks.JobStore",
        FakeJobStore,
    )

    monkeypatch.setattr(
        "app.tasks.media_tasks.S3Storage",
        FakeS3Storage,
    )

    monkeypatch.setattr(
        "app.tasks.media_tasks.FFmpegProcessor",
        FakeFFmpegProcessor,
    )

    result = process_media.run(job_id)

    assert result["job_id"] == job_id
    assert result["status"] == "completed"

    assert FakeJobStore.jobs[job_id]["status"] == "completed"

    output = FakeJobStore.jobs[job_id]["output"]

    assert "video" in output
    assert "thumbnail" in output


def test_process_media_job_not_found(monkeypatch):
    job_id = "missing-job"

    class FakeJobStore:
        def get_job(self, requested_job_id):
            return None

    class FakeS3Storage:
        pass

    monkeypatch.setattr(
        "app.tasks.media_tasks.JobStore",
        FakeJobStore,
    )

    monkeypatch.setattr(
        "app.tasks.media_tasks.S3Storage",
        FakeS3Storage,
    )

    with pytest.raises(ValueError, match="Job not found"):
        process_media.run(job_id)


def test_process_media_marks_job_failed_after_final_retry(monkeypatch):
    job_id = "failed-job"

    job = {
        "job_id": job_id,
        "filename": "input.png",
        "operation": "resize",
        "object_key": f"uploads/{job_id}/input.png",
        "status": "pending",
    }

    class FakeJobStore:
        jobs = {job_id: job.copy()}

        def get_job(self, requested_job_id):
            return self.jobs.get(requested_job_id)

        def update_status(self, requested_job_id, status):
            self.jobs[requested_job_id]["status"] = status

        def update_job(
            self,
            requested_job_id,
            status=None,
            output=None,
            error=None,
        ):
            if status is not None:
                self.jobs[requested_job_id]["status"] = status

            if output is not None:
                self.jobs[requested_job_id]["output"] = output

            if error is not None:
                self.jobs[requested_job_id]["error"] = error

            return self.jobs[requested_job_id]

    class FakeS3Storage:
        def download_file(self, object_name, file_path):
            raise RuntimeError("S3 download failed")

    monkeypatch.setattr(
        "app.tasks.media_tasks.JobStore",
        FakeJobStore,
    )

    monkeypatch.setattr(
        "app.tasks.media_tasks.S3Storage",
        FakeS3Storage,
    )

    with pytest.raises(
        RuntimeError,
        match="S3 download failed",
    ):
        process_media.apply(
            args=[job_id],
            throw=True,
            retries=3,
        )

    assert FakeJobStore.jobs[job_id]["status"] == "failed"
    assert FakeJobStore.jobs[job_id]["error"] == "S3 download failed"


def test_process_media_pillow_failure_marks_job_failed(monkeypatch):
    job_id = "pillow-failure-job"

    job = {
        "job_id": job_id,
        "filename": "input.png",
        "operation": "resize",
        "object_key": f"uploads/{job_id}/input.png",
        "status": "pending",
    }

    class FakeJobStore:
        jobs = {job_id: job.copy()}

        def get_job(self, requested_job_id):
            return self.jobs.get(requested_job_id)

        def update_status(self, requested_job_id, status):
            self.jobs[requested_job_id]["status"] = status

        def update_job(
            self,
            requested_job_id,
            status=None,
            output=None,
            error=None,
        ):
            if status is not None:
                self.jobs[requested_job_id]["status"] = status

            if output is not None:
                self.jobs[requested_job_id]["output"] = output

            if error is not None:
                self.jobs[requested_job_id]["error"] = error

            return self.jobs[requested_job_id]

    class FakeS3Storage:
        def download_file(self, object_name, file_path):
            Path(file_path).write_bytes(b"invalid image data")

    class FakeImageProcessor:
        def process(self, input_path, output_path):
            raise ValueError("Pillow processing failed")

    monkeypatch.setattr(
        "app.tasks.media_tasks.JobStore",
        FakeJobStore,
    )

    monkeypatch.setattr(
        "app.tasks.media_tasks.S3Storage",
        FakeS3Storage,
    )

    monkeypatch.setattr(
        "app.tasks.media_tasks.ImageProcessor",
        FakeImageProcessor,
    )

    with pytest.raises(
        ValueError,
        match="Pillow processing failed",
    ):
        process_media.run(job_id)

    assert FakeJobStore.jobs[job_id]["status"] == "failed"
    assert (
        FakeJobStore.jobs[job_id]["error"]
        == "Pillow processing failed"
    )
def test_process_media_ffmpeg_failure_marks_job_failed(monkeypatch):
    job_id = "ffmpeg-failure-job"

    job = {
        "job_id": job_id,
        "filename": "input.mp4",
        "operation": "resize",
        "object_key": f"uploads/{job_id}/input.mp4",
        "status": "pending",
    }

    class FakeJobStore:
        jobs = {job_id: job.copy()}

        def get_job(self, requested_job_id):
            return self.jobs.get(requested_job_id)

        def update_status(self, requested_job_id, status):
            self.jobs[requested_job_id]["status"] = status

        def update_job(
            self,
            requested_job_id,
            status=None,
            output=None,
            error=None,
        ):
            if status is not None:
                self.jobs[requested_job_id]["status"] = status

            if output is not None:
                self.jobs[requested_job_id]["output"] = output

            if error is not None:
                self.jobs[requested_job_id]["error"] = error

            return self.jobs[requested_job_id]

    class FakeS3Storage:
        def download_file(self, object_name, file_path):
            Path(file_path).write_bytes(b"fake video")

    class FakeFFmpegProcessor:
        def process(self, input_path, output_dir):
            raise RuntimeError("FFmpeg processing failed")

    monkeypatch.setattr(
        "app.tasks.media_tasks.JobStore",
        FakeJobStore,
    )

    monkeypatch.setattr(
        "app.tasks.media_tasks.S3Storage",
        FakeS3Storage,
    )

    monkeypatch.setattr(
        "app.tasks.media_tasks.FFmpegProcessor",
        FakeFFmpegProcessor,
    )

    with pytest.raises(
        RuntimeError,
        match="FFmpeg processing failed",
    ):
        process_media.run(job_id)

    assert FakeJobStore.jobs[job_id]["status"] == "failed"
    assert (
        FakeJobStore.jobs[job_id]["error"]
        == "FFmpeg processing failed"
    )
def test_process_media_s3_upload_failure_marks_job_failed(monkeypatch):
    job_id = "s3-upload-failure-job"

    job = {
        "job_id": job_id,
        "filename": "input.png",
        "operation": "resize",
        "object_key": f"uploads/{job_id}/input.png",
        "status": "pending",
    }

    class FakeJobStore:
        jobs = {job_id: job.copy()}

        def get_job(self, requested_job_id):
            return self.jobs.get(requested_job_id)

        def update_status(self, requested_job_id, status):
            self.jobs[requested_job_id]["status"] = status

        def update_job(
            self,
            requested_job_id,
            status=None,
            output=None,
            error=None,
        ):
            if status is not None:
                self.jobs[requested_job_id]["status"] = status

            if output is not None:
                self.jobs[requested_job_id]["output"] = output

            if error is not None:
                self.jobs[requested_job_id]["error"] = error

            return self.jobs[requested_job_id]

    class FakeS3Storage:
        def download_file(self, object_name, file_path):
            Path(file_path).write_bytes(b"fake image")

        def upload_file(self, file_path, object_name):
            raise RuntimeError("S3 upload failed")

    class FakeImageProcessor:
        def process(self, input_path, output_path):
            Path(output_path).write_bytes(b"processed image")
            return output_path

    monkeypatch.setattr(
        "app.tasks.media_tasks.JobStore",
        FakeJobStore,
    )

    monkeypatch.setattr(
        "app.tasks.media_tasks.S3Storage",
        FakeS3Storage,
    )

    monkeypatch.setattr(
        "app.tasks.media_tasks.ImageProcessor",
        FakeImageProcessor,
    )

    with pytest.raises(
        RuntimeError,
        match="S3 upload failed",
    ):
        process_media.run(job_id)

    assert FakeJobStore.jobs[job_id]["status"] == "failed"
    assert (
        FakeJobStore.jobs[job_id]["error"]
        == "S3 upload failed"
    )
def test_process_media_missing_s3_object_marks_job_failed(monkeypatch):
    job_id = "missing-s3-object-job"

    job = {
        "job_id": job_id,
        "filename": "input.png",
        "operation": "resize",
        "object_key": f"uploads/{job_id}/input.png",
        "status": "pending",
    }

    class FakeJobStore:
        jobs = {job_id: job.copy()}

        def get_job(self, requested_job_id):
            return self.jobs.get(requested_job_id)

        def update_status(self, requested_job_id, status):
            self.jobs[requested_job_id]["status"] = status

        def update_job(
            self,
            requested_job_id,
            status=None,
            output=None,
            error=None,
        ):
            if status is not None:
                self.jobs[requested_job_id]["status"] = status

            if output is not None:
                self.jobs[requested_job_id]["output"] = output

            if error is not None:
                self.jobs[requested_job_id]["error"] = error

            return self.jobs[requested_job_id]

    class FakeS3Storage:
        def download_file(self, object_name, file_path):
            raise FileNotFoundError(
                f"S3 object not found: {object_name}"
            )

    monkeypatch.setattr(
        "app.tasks.media_tasks.JobStore",
        FakeJobStore,
    )

    monkeypatch.setattr(
        "app.tasks.media_tasks.S3Storage",
        FakeS3Storage,
    )

    with pytest.raises(
        FileNotFoundError,
        match="S3 object not found",
    ):
        process_media.run(job_id)

    assert FakeJobStore.jobs[job_id]["status"] == "failed"
    assert "S3 object not found" in FakeJobStore.jobs[job_id]["error"]
def test_process_media_redis_failure(monkeypatch):
    job_id = "redis-failure-job"

    class FakeJobStore:
        def get_job(self, requested_job_id):
            raise RuntimeError("Redis connection failed")

    class FakeS3Storage:
        pass

    monkeypatch.setattr(
        "app.tasks.media_tasks.JobStore",
        FakeJobStore,
    )

    monkeypatch.setattr(
        "app.tasks.media_tasks.S3Storage",
        FakeS3Storage,
    )

    with pytest.raises(
        RuntimeError,
        match="Redis connection failed",
    ):
        process_media.run(job_id)
def test_process_media_transient_failure_retries(monkeypatch):
    job_id = "transient-failure-job"

    job = {
        "job_id": job_id,
        "filename": "input.png",
        "operation": "resize",
        "object_key": f"uploads/{job_id}/input.png",
        "status": "pending",
    }

    class FakeJobStore:
        jobs = {job_id: job.copy()}

        def get_job(self, requested_job_id):
            return self.jobs.get(requested_job_id)

        def update_status(self, requested_job_id, status):
            self.jobs[requested_job_id]["status"] = status

        def update_job(
            self,
            requested_job_id,
            status=None,
            output=None,
            error=None,
        ):
            if status is not None:
                self.jobs[requested_job_id]["status"] = status

            if output is not None:
                self.jobs[requested_job_id]["output"] = output

            if error is not None:
                self.jobs[requested_job_id]["error"] = error

            return self.jobs[requested_job_id]

    class FakeS3Storage:
        def download_file(self, object_name, file_path):
            raise ConnectionError("Temporary S3 connection failure")

    monkeypatch.setattr(
        "app.tasks.media_tasks.JobStore",
        FakeJobStore,
    )

    monkeypatch.setattr(
        "app.tasks.media_tasks.S3Storage",
        FakeS3Storage,
    )

    with pytest.raises(ConnectionError, match="Temporary S3 connection failure"):
        process_media.run(job_id)

    assert FakeJobStore.jobs[job_id]["status"] == "failed"
def test_process_media_cleans_up_temp_files_after_failure(monkeypatch):
    job_id = "cleanup-failure-job"

    job = {
        "job_id": job_id,
        "filename": "input.png",
        "operation": "resize",
        "object_key": f"uploads/{job_id}/input.png",
        "status": "pending",
    }

    created_paths = []

    class FakeJobStore:
        jobs = {job_id: job.copy()}

        def get_job(self, requested_job_id):
            return self.jobs.get(requested_job_id)

        def update_status(self, requested_job_id, status):
            self.jobs[requested_job_id]["status"] = status

        def update_job(
            self,
            requested_job_id,
            status=None,
            output=None,
            error=None,
        ):
            if status is not None:
                self.jobs[requested_job_id]["status"] = status

            if error is not None:
                self.jobs[requested_job_id]["error"] = error

            return self.jobs[requested_job_id]

    class FakeS3Storage:
        def download_file(self, object_name, file_path):
            path = Path(file_path)
            path.write_bytes(b"fake image")
            created_paths.append(path)

    class FakeImageProcessor:
        def process(self, input_path, output_path):
            raise ValueError("Processing failed")

    monkeypatch.setattr(
        "app.tasks.media_tasks.JobStore",
        FakeJobStore,
    )

    monkeypatch.setattr(
        "app.tasks.media_tasks.S3Storage",
        FakeS3Storage,
    )

    monkeypatch.setattr(
        "app.tasks.media_tasks.ImageProcessor",
        FakeImageProcessor,
    )

    with pytest.raises(ValueError, match="Processing failed"):
        process_media.run(job_id)

    assert FakeJobStore.jobs[job_id]["status"] == "failed"

    assert created_paths
    assert not created_paths[0].exists()
def test_process_media_new_job_succeeds_after_failed_job(monkeypatch):
    failed_job_id = "failed-job"
    successful_job_id = "recovery-job"

    jobs = {
        failed_job_id: {
            "job_id": failed_job_id,
            "filename": "bad.png",
            "operation": "resize",
            "object_key": f"uploads/{failed_job_id}/bad.png",
            "status": "pending",
        },
        successful_job_id: {
            "job_id": successful_job_id,
            "filename": "good.png",
            "operation": "resize",
            "object_key": f"uploads/{successful_job_id}/good.png",
            "status": "pending",
        },
    }

    class FakeJobStore:
        def get_job(self, requested_job_id):
            return jobs.get(requested_job_id)

        def update_status(self, requested_job_id, status):
            jobs[requested_job_id]["status"] = status

        def update_job(
            self,
            requested_job_id,
            status=None,
            output=None,
            error=None,
        ):
            if status is not None:
                jobs[requested_job_id]["status"] = status

            if output is not None:
                jobs[requested_job_id]["output"] = output

            if error is not None:
                jobs[requested_job_id]["error"] = error

            return jobs[requested_job_id]

    class FakeS3Storage:
        def download_file(self, object_name, file_path):
            if object_name.startswith(f"uploads/{failed_job_id}"):
                raise RuntimeError("S3 download failed")

            Path(file_path).write_bytes(b"fake image")

        def upload_file(self, file_path, object_name):
            assert Path(file_path).exists()

    class FakeImageProcessor:
        def process(self, input_path, output_path):
            Path(output_path).write_bytes(b"processed image")
            return output_path

    monkeypatch.setattr(
        "app.tasks.media_tasks.JobStore",
        FakeJobStore,
    )

    monkeypatch.setattr(
        "app.tasks.media_tasks.S3Storage",
        FakeS3Storage,
    )

    monkeypatch.setattr(
        "app.tasks.media_tasks.ImageProcessor",
        FakeImageProcessor,
    )

    # First job fails.
    with pytest.raises(
        RuntimeError,
        match="S3 download failed",
    ):
        process_media.run(failed_job_id)

    assert jobs[failed_job_id]["status"] == "failed"

    # A new job should still process successfully.
    result = process_media.run(successful_job_id)

    assert result["job_id"] == successful_job_id
    assert result["status"] == "completed"
    assert jobs[successful_job_id]["status"] == "completed"