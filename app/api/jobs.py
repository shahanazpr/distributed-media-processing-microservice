from fastapi import APIRouter
from pydantic import BaseModel
from uuid import uuid4

router = APIRouter(prefix="/jobs", tags=["Jobs"])


class JobRequest(BaseModel):
    filename: str
    operation: str


@router.post("")
async def create_job(request: JobRequest):
    job_id = str(uuid4())

    return {
        "job_id": job_id,
        "status": "queued",
        "filename": request.filename,
        "operation": request.operation
    }


@router.get("/{job_id}")
async def get_job(job_id: str):
    return {
        "job_id": job_id,
        "status": "queued"
    }