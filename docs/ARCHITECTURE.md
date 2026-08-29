# Service Architecture and Development Documentation

## Distributed Media Processing Microservice

## 1. Overview

The Distributed Media Processing Microservice is an event-driven backend service designed to handle heavy and asynchronous media-processing workloads.

The service accepts media-processing jobs from the main web application, processes them asynchronously using background workers, and stores optimized media assets in AWS S3.

The architecture is designed to keep the main application responsive while CPU-intensive media-processing operations are performed independently.

## 2. Service Architecture

The microservice consists of several components, each with a specific responsibility:

* **FastAPI** – Provides the REST API and accepts media-processing requests.
* **AWS S3** – Stores input media and processed media files.
* **RabbitMQ** – Acts as the message broker for distributing processing jobs.
* **Celery** – Handles asynchronous background processing.
* **Redis** – Stores job status and provides caching/result-backend support.
* **Pillow** – Used for image processing.
* **FFmpeg** – Used for video processing.

### Architecture Flow

```text
Client / Main Web Application
            |
            v
         FastAPI
         /      \
        v        v
     Redis    RabbitMQ
   Job Status     |
                  v
            Celery Worker
             /         \
            v           v
        Pillow        FFmpeg
       (Images)       (Videos)
             \         /
              v       v
                AWS S3
                  |
                  v
           Optimized Media
```

The RabbitMQ, Celery, Redis, Pillow, and FFmpeg components represent the planned asynchronous processing architecture and will be integrated as development progresses.

## 3. FastAPI Architecture

FastAPI acts as the API layer of the microservice.

Its responsibilities include:

* Accepting media-processing requests.
* Creating processing jobs.
* Providing job-status information.
* Providing a health-check endpoint.
* Communicating with the asynchronous processing pipeline.

### Current Implementation

The current FastAPI application is implemented in:

```text
app/main.py
```

The current implementation provides a health-check endpoint:

```text
GET /health
```

Example response:

```json
{
  "status": "healthy",
  "service": "media-processing-microservice"
}
```

### Planned Job APIs

The project plans to provide the following job-processing endpoints:

```text
POST /jobs
GET /jobs/{job_id}
```

* `POST /jobs` – Creates a media-processing job.
* `GET /jobs/{job_id}` – Retrieves the status of a processing job.

The job-status functionality is being developed toward Redis-backed status tracking.

## 4. AWS S3 Interaction

AWS S3 is used as the cloud storage layer for media files.

The S3 storage service is located at:

```text
app/storage/s3.py
```

The storage service is responsible for:

* Uploading media files.
* Downloading media files.
* Handling missing objects.
* Handling S3-related errors.
* Generating presigned URLs as the integration is completed.

### Media Storage Flow

```text
Input Media
     |
     v
   AWS S3
     |
     v
Celery Worker
     |
     v
Media Processing
     |
     v
Optimized Media
     |
     v
   AWS S3
```

AWS credentials must be provided through environment variables.

Credentials must never be hardcoded or committed to the repository.

## 5. Planned RabbitMQ and Celery Flow

RabbitMQ and Celery are planned to provide asynchronous job processing.

The intended processing flow is:

1. The client submits a media-processing job to FastAPI.
2. FastAPI creates the processing job.
3. The job status is stored in Redis.
4. The job is sent to RabbitMQ through Celery.
5. A Celery worker receives the job.
6. The worker downloads the media from S3.
7. Pillow or FFmpeg processes the media.
8. The optimized media is uploaded back to S3.
9. Redis is updated with the final job status.
10. The client retrieves the job status and result.

This architecture allows background workers to process CPU-intensive media operations independently from the main web application.

Multiple Celery workers can be added in the future to support scalable processing workloads.

## 6. Redis Role

Redis is planned to act as the job-status and caching layer.

Its responsibilities include:

* Storing the current status of processing jobs.
* Supporting job-status lookups.
* Acting as the Celery result backend.
* Providing fast access to temporary job information.

The planned job states are:

```text
PENDING
PROCESSING
COMPLETED
FAILED
```

The status flow is:

```text
PENDING
   |
   v
PROCESSING
   |
   +------> COMPLETED
   |
   +------> FAILED
```

## 7. Media Processing

The system is designed to support different processing tools for different media types.

### Images

Pillow will be used for operations such as:

* Cropping
* Resizing
* Compression
* Watermarking

### Videos

FFmpeg will be used for operations such as:

* Thumbnail extraction
* Video transcoding
* MP4 output
* H.264 encoding
* Video optimization

## 8. Error Handling and Retries

The system is designed to handle failures without blocking the main web application.

Expected failure scenarios include:

* S3 connection failures.
* Missing S3 objects.
* Network timeouts.
* Media-processing failures.
* RabbitMQ connection failures.
* Worker failures.

Celery retry mechanisms will be used for appropriate transient failures such as network-related errors.

## 9. Current Project Structure

The current project structure is:

```text
distributed-media-processing-microservice/
│
├── app/
│   ├── storage/
│   │   ├── s3.py
│   │   └── __init__.py
│   │
│   ├── main.py
│   └── __init__.py
│
├── tests/
│
├── docs/
│   └── ARCHITECTURE.md
│
├── .gitignore
├── LICENSE
└── README.md
```

Additional API, task, media-processing, and service modules will be added as implementation progresses.

## 10. Local Development Setup

### Prerequisites

The project requires:

* Python
* pip
* Git
* AWS configuration for S3 integration

### Clone the Repository

```bash
git clone https://github.com/shahanazpr/distributed-media-processing-microservice.git
cd distributed-media-processing-microservice
```

### Create a Virtual Environment

#### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

#### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

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

Do not commit the `.env` file to the repository.

### Run the FastAPI Application

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

### Run Tests

```bash
pytest
```

## 11. Docker Development

The completed system is intended to run using Docker Compose.

The planned services include:

```text
FastAPI
Celery Worker
RabbitMQ
Redis
```

The Celery worker container will include the required media-processing dependencies, including FFmpeg.

The Docker setup will be finalized as infrastructure development progresses.

## 12. Component Responsibilities

| Component | Responsibility | Status |
|---|---|---|
| FastAPI | REST API and request handling | Implemented |
| AWS S3 | Media storage | Implemented |
| RabbitMQ | Message brokering | Planned |
| Celery | Asynchronous task processing | Planned |
| Redis | Job status and result backend | Planned |
| Pillow | Image processing | Planned |
| FFmpeg | Video processing | Planned |

## 13. Overall Architecture Summary

The planned architecture separates API handling, job management, asynchronous processing, media processing, and cloud storage responsibilities.

```text
                    +----------------------+
                    | Client / Main Web App|
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |       FastAPI        |
                    |      REST API        |
                    +----+-------------+---+
                         |             |
                         v             v
                   +----------+   +----------+
                   |  Redis   |   | RabbitMQ |
                   | Job      |   |  Broker  |
                   | Status   |   +----+-----+
                   +----------+        |
                                       v
                                +-------------+
                                |   Celery    |
                                |   Worker    |
                                +------+------+
                                       |
                              +--------+--------+
                              |                 |
                              v                 v
                         +---------+       +---------+
                         | Pillow  |       | FFmpeg  |
                         | Images  |       | Videos  |
                         +----+----+       +----+----+
                              |                 |
                              +--------+--------+
                                       |
                                       v
                                +-------------+
                                |   AWS S3    |
                                |Media Storage|
                                +-------------+
```

## 14. Development Status

The project is currently under active development.

The current foundation includes:

* FastAPI application scaffolding.
* Health-check endpoint.
* Initial project structure.
* Initial automated testing.
* S3 storage service implementation.

RabbitMQ, Celery, Redis-backed job tracking, media-processing components, Docker infrastructure, and monitoring will be integrated incrementally as the team completes the assigned development issues.