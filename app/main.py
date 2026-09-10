from fastapi import FastAPI, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.api.jobs import router as jobs_router

app = FastAPI(
    title="Distributed Media Processing Microservice",
    description="Event-driven microservice for asynchronous media processing.",
    version="1.0.0",
)

app.include_router(jobs_router)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "media-processing-microservice"
    }


@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)