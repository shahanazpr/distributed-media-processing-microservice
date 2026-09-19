from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.jobs import router as jobs_router


app = FastAPI(
    title="Distributed Media Processing Microservice",
    description="Event-driven microservice for asynchronous media processing.",
    version="1.0.0",
)

app.include_router(jobs_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )