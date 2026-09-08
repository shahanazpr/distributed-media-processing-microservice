import tempfile
from pathlib import Path

from app.media.image_processor import validate_image
from app.processing.ffmpeg import FFmpegProcessor
from app.services.job_store import JobStore
from app.storage.s3 import S3Storage
from app.tasks.celery_app import celery_app


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


@celery_app.task(
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def process_media(self, job_id: str) -> dict:
    """
    Process an image or video job using Celery.

    Flow:
    1. Retrieve job from Redis
    2. Set status to PROCESSING
    3. Download input from S3
    4. Detect media type
    5. Process using Pillow or FFmpeg
    6. Upload output to S3
    7. Update Redis to COMPLETED
    8. Mark FAILED when processing fails
    """

    job_store = JobStore()

    job = job_store.get_job(job_id)

    if job is None:
        raise ValueError(f"Job not found: {job_id}")

    storage = S3Storage()

    job_store.update_status(job_id, "PROCESSING")

    filename = job["filename"]
    object_key = job["object_key"]

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

            # Download input media from S3
            storage.download_file(
                object_key,
                str(input_path),
            )

            # -------------------------
            # IMAGE PROCESSING
            # -------------------------
            if extension in IMAGE_EXTENSIONS:

                image = validate_image(
                    str(input_path)
                )

                output_path = (
                    output_dir
                    / f"{Path(filename).stem}_processed.jpg"
                )

                image.save(
                    output_path,
                    format="JPEG",
                    quality=85,
                    optimize=True,
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

            # -------------------------
            # VIDEO PROCESSING
            # -------------------------
            elif extension in VIDEO_EXTENSIONS:

                processor = FFmpegProcessor()

                results = processor.process(
                    str(input_path),
                    str(output_dir),
                )

                output = {}

                for output_type, output_path in results.items():

                    output_key = (
                        f"outputs/{job_id}/{Path(output_path).name}"
                    )

                    storage.upload_file(
                        output_path,
                        output_key,
                    )

                    output[output_type] = {
                        "object_key": output_key
                    }

            else:
                raise ValueError(
                    f"Unsupported media type: {extension}"
                )

        # Update Redis with completed status and output
        job_store.update_job(
            job_id=job_id,
            status="COMPLETED",
            output=output,
        )

        return {
            "job_id": job_id,
            "status": "COMPLETED",
            "output": output,
        }

    except Exception as exc:

        # Update Redis with failed status and error
        job_store.update_job(
            job_id=job_id,
            status="FAILED",
            error=str(exc),
        )

        raise