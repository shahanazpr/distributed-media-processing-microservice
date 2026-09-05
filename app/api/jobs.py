from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel

from app.storage.s3 import S3Storage

router = APIRouter(prefix="/jobs", tags=["Jobs"])


class JobRequest(BaseModel):
    filename: str
    operation: Literal["resize"]


@router.post("")
async def create_job(request: JobRequest):
    job_id = str(uuid4())

    # Generate a unique S3 object key
    filename = Path(request.filename).name
    object_key = f"uploads/{job_id}/{filename}"

    # Generate a presigned upload URL through the S3 storage service
    storage = S3Storage()
    upload_url = storage.generate_presigned_upload_url(object_key)

    return {
        "job_id": job_id,
        "status": "pending",
        "filename": request.filename,
        "operation": request.operation,
        "upload_url": upload_url,
        "object_key": object_key,
    }


@router.get("/{job_id}")
async def get_job(job_id: str):
    return {
        "job_id": job_id,
        "status": "pending",
    }