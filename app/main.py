from fastapi import FastAPI

app = FastAPI(
    title="Distributed Media Processing Microservice",
    description="Event-driven microservice for asynchronous media processing.",
    version="1.0.0",
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "media-processing-microservice"
    }