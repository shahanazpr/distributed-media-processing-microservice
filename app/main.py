import logging

from fastapi import FastAPI

from app.api.jobs import router as jobs_router
from app.core.logging import setup_logging


setup_logging()

logger = logging.getLogger(__name__)


app = FastAPI(
    title="Distributed Media Processing Microservice",
    description="Event-driven microservice for asynchronous media processing.",
    version="1.0.0",
)


@app.get("/health")
async def health_check():
    logger.info("Health check requested")

    return {
        "status": "healthy",
        "service": "media-processing-microservice"
    }


app.include_router(jobs_router)