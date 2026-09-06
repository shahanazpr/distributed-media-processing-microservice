from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import uuid4

from app.services.job_status_service import (
    create_job,
    get_job,
    JobStatusError,
)


router = APIRouter(prefix="/jobs", tags=["Jobs"])


class JobRequest(BaseModel):
    filename: str
    operation: str


@router.post("")
async def create_job_endpoint(request: JobRequest):
    job_id = str(uuid4())

    try:
        job = create_job(
            job_id=job_id,
            filename=request.filename,
            operation=request.operation,
        )
    except JobStatusError:
        raise HTTPException(
            status_code=503,
            detail="Job status service unavailable"
        )

    return job


@router.get("/{job_id}")
async def get_job_status(job_id: str):
    try:
        job = get_job(job_id)
    except JobStatusError:
        raise HTTPException(
            status_code=503,
            detail="Job status service unavailable"
        )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    return job