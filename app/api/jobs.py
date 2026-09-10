from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.job_store import JobStore
from app.storage.s3 import S3Storage
from app.tasks.media_tasks import process_media


router = APIRouter(prefix="/jobs", tags=["Jobs"])


class JobRequest(BaseModel):
    filename: str
    operation: Literal["resize"]


@router.post("")
async def create_job(request: JobRequest):
    job_id = str(uuid4())

    filename = Path(request.filename).name
    object_key = f"uploads/{job_id}/{filename}"

    storage = S3Storage()
    upload_url = storage.generate_presigned_upload_url(object_key)

    job_store = JobStore()

    job_store.create_job(
        job_id=job_id,
        filename=filename,
        operation=request.operation,
        object_key=object_key,
        status="pending",
    )

    return {
        "job_id": job_id,
        "status": "pending",
        "filename": filename,
        "operation": request.operation,
        "upload_url": upload_url,
        "object_key": object_key,
    }


@router.post("/{job_id}/confirm-upload")
async def confirm_upload(job_id: str):
    job_store = JobStore()

    job = job_store.get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    if job["status"] != "pending":
        raise HTTPException(
            status_code=400,
            detail="Job is not pending",
        )

    storage = S3Storage()

    if not storage.object_exists(job["object_key"]):
        raise HTTPException(
            status_code=400,
            detail="Upload not completed",
        )

    process_media.delay(job_id)

    return {
        "job_id": job_id,
        "status": "processing",
    }


@router.get("/{job_id}")
async def get_job(job_id: str):
    job_store = JobStore()

    job = job_store.get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return job