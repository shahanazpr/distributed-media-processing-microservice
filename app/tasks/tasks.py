import os
import tempfile

from PIL import Image

from app.tasks.celery_app import celery_app
from app.services.job_store import JobStore
from app.storage.s3 import S3Storage


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def process_media(self, job_id: str):
    job_store = JobStore()
    storage = S3Storage()

    job = job_store.get_job(job_id)

    if job is None:
        raise ValueError(f"Job not found: {job_id}")

    job_store.update_status(job_id, "processing")

    try:
        filename = job["filename"]
        operation = job["operation"]
        object_key = job["object_key"]

        print(f"Processing media job: {job_id}")
        print(f"File: {filename}")
        print(f"Operation: {operation}")

        if operation != "resize":
            raise ValueError(f"Unsupported operation: {operation}")

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = os.path.join(temp_dir, filename)
            output_path = os.path.join(temp_dir, f"processed_{filename}")

            storage.download_file(object_key, input_path)

            with Image.open(input_path) as image:
                image.thumbnail((1280, 1280))

                if image.format == "JPEG":
                    image.save(output_path, format="JPEG", quality=85)
                else:
                    image.save(output_path)

            output_key = f"processed/{job_id}/{filename}"
            storage.upload_file(output_path, output_key)

        job_store.update_output(job_id, output_key)
        job_store.update_status(job_id, "completed")

        return {
            "job_id": job_id,
            "status": "completed",
            "output_key": output_key,
        }

    except Exception:
        job_store.update_status(job_id, "failed")
        raise