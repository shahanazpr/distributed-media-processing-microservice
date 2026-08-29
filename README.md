# Distributed Media Processing Microservice

An event-driven backend microservice designed to handle heavy, asynchronous media-processing workloads.

The service is responsible for accepting media-processing jobs from a main web application, processing media asynchronously using Celery workers, and storing optimized media assets in cloud storage.

## Project Overview

The microservice offloads CPU-intensive media-processing tasks from the primary web application.

Instead of making the main application wait for operations such as image resizing or video transcoding, the application submits a job to this service. The job is placed into an asynchronous processing pipeline and handled by background workers.

### Main Processing Flow

Client / Main Web Application
        |
        v
     FastAPI
        |
        +------> Redis (Job Status)
        |
        v
    RabbitMQ
        |
        v
   Celery Worker
        |
        +------> Pillow (Images)
        |
        +------> FFmpeg (Videos)
        |
        v
      AWS S3
        |
        v
   Optimized Media

## Key Features

- FastAPI REST API for submitting and tracking processing jobs
- Asynchronous background processing with Celery
- RabbitMQ message broker for distributing jobs
- Redis for job-status tracking and caching
- AWS S3 for media storage
- Pillow for image processing
- FFmpeg for video processing
- Docker-based deployment
- Prometheus metrics and monitoring
- Retry and error-handling mechanisms for asynchronous jobs
- Scalable worker-based architecture

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| API Framework | FastAPI |
| Task Queue | Celery |
| Message Broker | RabbitMQ |
| Cache / Job Status | Redis |
| Image Processing | Pillow |
| Video Processing | FFmpeg / FFmpeg-python |
| Cloud Storage | AWS S3 |
| AWS SDK | Boto3 |
| Containerization | Docker / Docker Compose |
| Monitoring | Prometheus |
| Testing | Pytest |

## Project Structure

```text
distributed-media-processing-microservice/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── jobs.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   └── logging.py
│   │
│   ├── media/
│   ├── services/
│   ├── storage/
│   └── tasks/
│
├── tests/
│   ├── __init__.py
│   └── test_health.py
│
├── .env.example
├── .gitignore
├── requirements.txt
├── docker-compose.yml
└── README.md
```

The exact contents of the directories will grow as the project implementation progresses.

## Current API

### Health Check

```http
GET /health
```

Example response:

```json
{
  "status": "healthy",
  "service": "media-processing-microservice"
}
```

### Create Processing Job

```http
POST /jobs
```

Current request format:

```json
{
  "filename": "image.jpg",
  "operation": "resize"
}
```

Current response format:

```json
{
  "job_id": "generated-uuid",
  "status": "queued",
  "filename": "image.jpg",
  "operation": "resize"
}
```

### Get Job Status

```http
GET /jobs/{job_id}
```

The job-status endpoint is being developed toward Redis-backed status tracking as the asynchronous processing pipeline is integrated.

## Media Processing

### Images

Image processing will use Pillow for operations such as:

- Cropping
- Resizing
- Compression
- Watermarking

### Videos

Video processing will use FFmpeg for operations such as:

- Thumbnail extraction
- Video transcoding
- MP4 output
- H.264 encoding
- Video optimization

## Storage

AWS S3 is used as the media storage layer.

The storage service provides functionality for:

- Uploading files
- Downloading files
- Handling missing objects
- Handling S3 errors
- Generating presigned URLs as the API/storage integration is completed

AWS configuration must be provided through environment variables. Credentials must never be hardcoded or committed to the repository.

## Asynchronous Processing Architecture

The intended processing pipeline is:

1. Client submits a media-processing job.
2. FastAPI creates the job.
3. Job status is stored in Redis.
4. The job is sent to the RabbitMQ queue through Celery.
5. A Celery worker receives the job.
6. The worker downloads the media from S3.
7. Pillow or FFmpeg processes the media.
8. The optimized asset is uploaded back to S3.
9. Redis is updated with the final job status.
10. The client can retrieve the job status and result.

## Job States

Jobs will use the following states:

```text
PENDING
PROCESSING
COMPLETED
FAILED
```

## Error Handling and Retries

The system is designed to handle failures without blocking the main web application.

Expected failure scenarios include:

- S3 connection failures
- Missing S3 objects
- Network timeouts
- Media-processing failures
- RabbitMQ connection failures
- Worker failures

Celery retry mechanisms will be used for appropriate transient failures such as network-related errors.

## Development Setup

### 1. Clone the repository

```bash
git clone https://github.com/shahanazpr/distributed-media-processing-microservice.git
cd distributed-media-processing-microservice
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Linux / macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file based on `.env.example`.

Example configuration:

```env
AWS_REGION=ap-south-1
S3_BUCKET_NAME=your-bucket-name

REDIS_URL=redis://localhost:6379/0

RABBITMQ_URL=amqp://guest:guest@localhost:5672//
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

Do not commit the `.env` file.

## Running the FastAPI Application

Start the development server with:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

OpenAPI specification:

```text
http://127.0.0.1:8000/openapi.json
```

## Running Tests

Run the test suite with:

```bash
pytest
```

The project uses Pytest for automated testing of the application and storage components.

## Docker

The completed system is intended to run using Docker Compose with services including:

```text
FastAPI
Celery Worker
RabbitMQ
Redis
```

The worker container will also include the required media-processing dependencies, including FFmpeg.

The Docker setup will be finalized as infrastructure work progresses.

## Monitoring

Prometheus metrics will be added to monitor the asynchronous processing system.

Planned metrics include:

- Number of jobs
- Successful jobs
- Failed jobs
- Processing duration
- Queue activity
- Worker activity

## Git Workflow

Development is organized using feature branches.

Example:

```text
main
  |
  +-- feature/job-api
  +-- feature/s3-storage-service
  +-- feature/configuration
  +-- feature/s3-tests
  +-- feature/architecture-docs
```

Changes should be developed on feature branches and reviewed through Pull Requests before being merged into the main project branch.

## Team Development

This project is being developed as a team project. Work is divided into GitHub Issues so that API development, cloud storage, configuration, testing, media processing, infrastructure, and documentation can progress in parallel.

## Project Goals

The completed microservice should:

- Keep the primary web application responsive
- Process CPU-intensive media tasks asynchronously
- Support scalable background workers
- Reliably store input and output media
- Track job status
- Handle transient failures and retries
- Provide monitoring and operational visibility
- Support containerized deployment

## Project Status

Development is currently in progress.

Completed foundation work includes:

- FastAPI application scaffolding
- Health-check endpoint
- Initial Jobs API
- Basic application structure
- Initial automated testing
- S3 storage service implementation

The remaining components will be integrated incrementally as the team completes the assigned development issues.
