import tempfile
from pathlib import Path

<<<<<<< HEAD
from app.media.image_processor import validate_image
from app.processing.ffmpeg import FFmpegProcessor
=======
from botocore.exceptions import (
    ConnectionClosedError,
    ConnectTimeoutError,
    EndpointConnectionError,
    ReadTimeoutError,
)

from app.processing.ffmpeg import FFmpegProcessor
from app.processing.image import ImageProcessor
>>>>>>> origin/develop
from app.services.job_store import JobStore
from app.storage.s3 import S3Storage
from app.tasks.celery_app import celery_app


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}

<<<<<<< HEAD

@celery_app.task(
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
=======
TRANSIENT_ERRORS = (
    ConnectionClosedError,
    ConnectTimeoutError,
    EndpointConnectionError,
    ReadTimeoutError,
)


@celery_app.task(
    bind=True,
    autoretry_for=TRANSIENT_ERRORS,
>>>>>>> origin/develop
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def process_media(self, job_id: str) -> dict:
    """
<<<<<<< HEAD
    Process an image or video job asynchronously.

    Flow:
    1. Retrieve job from Redis.
    2. Set status to PROCESSING.
    3. Download input from S3.
    4. Detect media type.
    5. Process using Pillow or FFmpeg.
    6. Upload processed output to S3.
    7. Set status to COMPLETED.
    8. Set status to FAILED when processing fails.
    """

    job_store = JobStore()
=======
    Process a media job asynchronously.

    Flow:
        Redis pending
        -> Redis processing
        -> Download from S3
        -> Pillow / FFmpeg processing
        -> Upload output to S3
        -> Redis completed
    """

    job_store = JobStore()
    storage = S3Storage()

>>>>>>> origin/develop
    job = job_store.get_job(job_id)

    if job is None:
        raise ValueError(f"Job not found: {job_id}")

<<<<<<< HEAD
    storage = S3Storage()

=======
>>>>>>> origin/develop
    job_store.update_status(job_id, "processing")

    filename = job["filename"]
    object_key = job["object_key"]
<<<<<<< HEAD
=======

>>>>>>> origin/develop
    extension = Path(filename).suffix.lower()

    try:
        with tempfile.TemporaryDirectory(
            prefix=f"media_job_{job_id}_"
        ) as temp_dir:

            input_path = Path(temp_dir) / filename

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

<<<<<<< HEAD
            # Download input media from S3.
=======
            # Download input media from S3
>>>>>>> origin/develop
            storage.download_file(
                object_key,
                str(input_path),
            )

<<<<<<< HEAD
            # -------------------------
            # IMAGE PROCESSING
            # -------------------------
            if extension in IMAGE_EXTENSIONS:

                image = validate_image(str(input_path))

                output_path = (
                    output_dir
                    / f"{Path(filename).stem}_processed.jpg"
                )

                image.save(
                    output_path,
                    format="JPEG",
                    quality=85,
                    optimize=True,
=======
            # Image processing using Pillow
            if extension in IMAGE_EXTENSIONS:
                output_path = (
                    output_dir
                    / f"{Path(filename).stem}_resized.jpg"
                )

                processor = ImageProcessor()

                processor.process(
                    str(input_path),
                    str(output_path),
>>>>>>> origin/develop
                )

                output_key = (
                    f"outputs/{job_id}/{output_path.name}"
                )

                storage.upload_file(
                    str(output_path),
                    output_key,
                )

                output = {
                    "type": "image",
                    "object_key": output_key,
                }

<<<<<<< HEAD
            # -------------------------
            # VIDEO PROCESSING
            # -------------------------
            elif extension in VIDEO_EXTENSIONS:

=======
            # Video processing using FFmpeg
            elif extension in VIDEO_EXTENSIONS:
>>>>>>> origin/develop
                processor = FFmpegProcessor()

                results = processor.process(
                    str(input_path),
                    str(output_dir),
                )

                output = {}

                for output_type, output_path in results.items():
<<<<<<< HEAD

=======
>>>>>>> origin/develop
                    output_key = (
                        f"outputs/{job_id}/{Path(output_path).name}"
                    )

                    storage.upload_file(
                        output_path,
                        output_key,
                    )

                    output[output_type] = {
                        "object_key": output_key,
                    }

            else:
                raise ValueError(
                    f"Unsupported media type: {extension}"
                )

<<<<<<< HEAD
        job_store.update_job(
            job_id=job_id,
=======
        # Save completed status and output in Redis
        job_store.update_job(
            job_id,
>>>>>>> origin/develop
            status="completed",
            output=output,
        )

        return {
            "job_id": job_id,
            "status": "completed",
            "output": output,
        }

<<<<<<< HEAD
    except Exception as exc:

        job_store.update_job(
            job_id=job_id,
=======
    except TRANSIENT_ERRORS as exc:
        # Celery automatically retries transient S3/network errors.
        # Mark the job as failed only after the final retry.
        if self.request.retries >= 3:
            job_store.update_job(
                job_id,
                status="failed",
                error=str(exc),
            )

        raise

    except Exception as exc:
        # Permanent processing errors are marked as failed.
        job_store.update_job(
            job_id,
>>>>>>> origin/develop
            status="failed",
            error=str(exc),
        )

<<<<<<< HEAD
        raise
=======
        raise
>>>>>>> origin/develop
