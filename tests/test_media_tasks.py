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
            Path(file_path).write_bytes(b"fake image")

        def upload_file(self, file_path, object_name):
            assert Path(file_path).exists()
            assert object_name.startswith(f"outputs/{job_id}/")

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

    result = process_media.run(job_id)

    assert result["job_id"] == job_id
    assert result["status"] == "completed"

    assert FakeJobStore.jobs[job_id]["status"] == "completed"
    assert "output" in FakeJobStore.jobs[job_id]


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