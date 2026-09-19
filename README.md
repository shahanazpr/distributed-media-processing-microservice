# Distributed Media Processing Microservice

An event-driven backend microservice for handling heavy, asynchronous media-processing workloads.

## Project Overview

This microservice offloads CPU-intensive media-processing operations from the primary web application. Clients submit jobs through FastAPI, media is stored in S3-compatible object storage, and processing is performed asynchronously by Celery workers through RabbitMQ. Redis tracks job status, while processed assets are stored in object storage and can be delivered through CloudFront when configured.

## Architecture

```text
Client / Main Web Application
            |
            v
        FastAPI API
        /        \
       v          v
    Redis        S3 / MinIO
  Job Status   Input Media
       |
       v
    RabbitMQ
       |
       v
  Celery Workers
       |
   +---+----------------+
   |                    |
   v                    v
 Pillow              FFmpeg
 Images              Videos
   |                    |
   +---------+----------+
             |
             v
       S3 / MinIO Output
             |
             v
        CloudFront
             |
             v
           Client

Prometheus monitors application and processing metrics.
```

## Key Features

- FastAPI REST API for job submission and status tracking
- Pre-signed S3 upload URLs
- Redis-backed job status tracking
- RabbitMQ message broker
- Celery asynchronous workers
- Pillow image processing
- FFmpeg video processing
- Image crop, resize, compression, and watermarking
- Video thumbnail extraction and MP4/H.264 transcoding
- Video watermarking
- S3-compatible input and output storage
- CloudFront CDN support
- Retry and failure handling
- Multiple Celery workers
- Docker Compose deployment
- Prometheus monitoring
- Pytest automated testing
- GitHub Actions CI
- Load and performance testing support

## Technology Stack

| Component | Technology |
|---|---|
| Language | Python |
| API Framework | FastAPI |
| Task Queue | Celery |
| Message Broker | RabbitMQ |
| Job Status / Cache | Redis |
| Image Processing | Pillow |
| Video Processing | FFmpeg / FFmpeg-python |
| Object Storage | AWS S3 / MinIO |
| AWS SDK | Boto3 |
| CDN | AWS CloudFront |
| Containerization | Docker / Docker Compose |
| Monitoring | Prometheus |
| Testing | Pytest |
| CI | GitHub Actions |

## End-to-End Workflow

1. Client requests a processing job.
2. FastAPI validates the request and creates a unique job ID.
3. FastAPI generates a pre-signed S3 upload URL.
4. Client uploads the original media directly to S3-compatible storage.
5. The processing task is sent to Celery through RabbitMQ.
6. Redis records the job as `pending`.
7. A Celery worker receives the task.
8. The worker changes the job status to `processing`.
9. The worker downloads the input media from object storage.
10. Pillow or FFmpeg processes the media.
11. Watermarking is applied when the selected processing flow supports it.
12. The processed file is uploaded to object storage.
13. Redis is updated with `completed` or `failed` status.
14. The job result contains processed output information.
15. The client retrieves the result through the job-status API.

## Job States

```text
pending -> processing -> completed
                                               -> failed
```

Transient failures can be retried according to the configured Celery retry policy.

## API

### Health Check

```http
GET /health
```

Example:

```json
{
  "status": "healthy"
}
```

### Create Processing Job

```http
POST /jobs
```

Example request:

```json
{
  "filename": "image.jpg",
  "operation": "resize"
}
```

The endpoint returns:

- Job ID
- Job status
- Filename
- Processing operation
- Pre-signed upload URL
- Object key

### Get Job Status

```http
GET /jobs/{job_id}
```

The response contains the current job information and, after successful processing, the processed output key.

### Trigger Processing

```http
POST /jobs/{job_id}/process
```

This verifies that the input media exists and submits the processing task to Celery.

## API Documentation

When running locally or through Docker:

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- OpenAPI specification: http://localhost:8000/openapi.json
- Metrics: http://localhost:8000/metrics

## Image Processing

Pillow is used for image processing operations such as:

- Cropping
- Resizing
- Compression
- JPEG output generation
- Watermarking

The currently verified Docker end-to-end workflow includes image resize processing.

## Video Processing

FFmpeg is used for:

- Thumbnail extraction
- Video transcoding
- MP4 output
- H.264 encoding
- Video optimization
- Watermarking

Video processing components are part of the project and should be validated through the corresponding integration tests before being marked as fully end-to-end verified.

## Storage

AWS S3 is used for production object storage. MinIO provides S3-compatible storage for local Docker development and integration testing.

The storage service supports:

- Uploads
- Downloads
- Object existence checks
- Pre-signed upload URL generation

Example object layout:

```text
uploads/<job_id>/original-file.jpg
processed/<job_id>/processed-file.jpg
```

Never hardcode or commit AWS credentials.

## CloudFront CDN

Processed media can be delivered through CloudFront when configured.

```text
S3 Output -> CloudFront -> Client
```

### Configuration

| Variable | Description |
|---|---|
| `CLOUDFRONT_DOMAIN` | CloudFront distribution domain |

If CloudFront is not configured, the application can continue to operate using the object-storage output.

The CloudFront helper is implemented and unit-tested. Full worker-level CDN URL integration should be verified separately before considering CloudFront delivery fully end-to-end.

## Asynchronous Processing

Celery executes processing outside the FastAPI request-response cycle.

RabbitMQ distributes tasks to Celery workers, while Redis is used as the result backend and for job status storage.

The unified processing task is:

```text
app.tasks.tasks.process_media
```

Multiple Celery workers can be started to process jobs concurrently.

### Local Celery Worker

```bash
celery -A app.tasks.celery_app.celery_app worker --loglevel=info
```

## Error Handling and Retries

The system is designed to handle:

- S3 connection and transfer failures
- Missing S3 objects
- Network timeouts
- Invalid media
- Corrupted images or videos
- Pillow failures
- FFmpeg failures
- RabbitMQ/Celery failures
- Worker failures

Transient failures are retried according to the configured Celery retry policy.

## Monitoring

Prometheus provides operational metrics.

### Metrics Endpoint

```text
http://localhost:8000/metrics
```

### Prometheus

When using Docker Compose:

```text
http://localhost:9090
```

Tracked application metrics include:

| Metric | Type | Description |
|---|---|---|
| `media_jobs_total` | Counter | Total jobs received |
| `media_jobs_succeeded_total` | Counter | Jobs completed successfully |
| `media_jobs_failed_total` | Counter | Jobs that failed |
| `media_job_status_total` | Counter | Jobs by status |
| `media_job_processing_duration_seconds` | Histogram | Time spent processing jobs |
| `media_queue_published_total` | Counter | Messages published to RabbitMQ |

## Docker Compose

The Docker Compose environment includes:

- FastAPI
- Celery worker
- RabbitMQ
- Redis
- MinIO
- Prometheus

### Start the Complete Stack

Build and start:

```bash
docker compose up --build
```

Or start in detached mode:

```bash
docker compose up -d --build
```

### Check Services

```bash
docker compose ps
```

Expected services:

| Service | Purpose |
|---|---|
| `api` | FastAPI application |
| `worker` | Celery media-processing worker |
| `redis` | Job status and Celery result backend |
| `rabbitmq` | Celery message broker |
| `minio` | S3-compatible object storage |
| `prometheus` | Monitoring |

Redis, RabbitMQ, and MinIO have Docker health checks.

### Service URLs

| Service | URL |
|---|---|
| FastAPI | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| Metrics | http://localhost:8000/metrics |
| Prometheus | http://localhost:9090 |
| MinIO API | http://localhost:9000 |
| MinIO Console | http://localhost:9001 |
| RabbitMQ Management | http://localhost:15672 |

### View Logs

All services:

```bash
docker compose logs -f
```

API:

```bash
docker compose logs api --tail=50
```

Worker:

```bash
docker compose logs worker --tail=50
```

### Verify Celery Worker

Check registered tasks:

```bash
docker compose exec worker celery -A app.tasks.celery_app.celery_app inspect registered
```

The worker should register:

```text
app.tasks.tasks.process_media
```

Check the worker user:

```bash
docker compose exec worker id
```

The worker runs as the non-root `appuser`.

### Restart an Individual Service

For example:

```bash
docker compose restart worker
```

Then check:

```bash
docker compose logs worker --tail=40
```

The worker should reconnect to RabbitMQ and become ready.

### Stop the Stack

```bash
docker compose down
```

### Restart the Complete Stack

```bash
docker compose down
docker compose up -d
docker compose ps
```

All required services should return to the running state. Redis, RabbitMQ, and MinIO should report healthy.

## Docker End-to-End Verification

The Docker deployment has been verified using the following workflow:

1. Start the Docker Compose stack.
2. Confirm all six services are running.
3. Verify the FastAPI health endpoint.
4. Create a processing job through the API.
5. Upload the input image using the generated pre-signed URL.
6. Trigger processing.
7. RabbitMQ delivers the task to Celery.
8. The Celery worker downloads the media from MinIO.
9. Pillow performs image resizing.
10. The processed image is uploaded back to MinIO.
11. Redis records the completed job and output key.
12. The processed output is verified in MinIO.
13. The worker is restarted and recovery is verified.
14. The complete Docker Compose stack is stopped and restarted successfully.
15. Prometheus and the application metrics endpoint are available.

The verified Docker worker runs as:

```text
uid=1000(appuser)
gid=1000(appuser)
```

The worker also successfully registers:

```text
app.tasks.tasks.process_media
```

## Local Development

### Clone

```bash
git clone https://github.com/shahanazpr/distributed-media-processing-microservice.git
cd distributed-media-processing-microservice
```

### Create a Virtual Environment on Windows

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

Copy `.env.example` to `.env` and configure the required values.

Never commit `.env` or real credentials.

## Environment Variables

Use the exact variable names implemented by the application.

Typical configuration includes:

```text
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION
S3_BUCKET_NAME
S3_ENDPOINT_URL
S3_PUBLIC_ENDPOINT_URL
REDIS_HOST
REDIS_PORT
RABBITMQ_HOST
RABBITMQ_PORT
RABBITMQ_USER
RABBITMQ_PASSWORD
CLOUDFRONT_DOMAIN
```

For local Docker development, the Compose configuration uses:

```text
Redis: redis:6379
RabbitMQ: rabbitmq:5672
MinIO: minio:9000
```

## Running the Application Locally

### FastAPI

```bash
uvicorn app.main:app --reload
```

Application:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

### Celery

```bash
celery -A app.tasks.celery_app.celery_app worker --loglevel=info
```

For Docker, use the worker service provided by Docker Compose.

## Testing

Run all tests:

```bash
pytest
```

Verbose output:

```bash
pytest -v
```

Tests should cover:

- FastAPI endpoints
- Job creation and status retrieval
- Redis job storage
- S3 operations
- Pre-signed URLs
- Pillow processing
- FFmpeg processing
- Watermarking
- Celery tasks
- Retry and failure behavior
- S3 input/output workflow
- End-to-end processing

## Continuous Integration

GitHub Actions is used for automated validation on pushes and pull requests.

The CI workflow should:

1. Install project dependencies.
2. Run the automated test suite.
3. Report test results.

Pull requests should be reviewed and required CI checks should pass before merging.

## Load Testing and Performance

The final system should be tested with:

- Multiple simultaneous job submissions
- Multiple image jobs
- Multiple video jobs
- Mixed image/video workloads
- Multiple Celery workers
- Failed jobs
- Retry scenarios
- Queue behavior under load
- S3 operations under load

Measure:

- API response time
- Queue waiting time
- Job processing time
- Worker CPU usage
- Memory usage
- S3 download/upload time
- Image processing time
- Video processing time

Performance optimization should focus on worker concurrency, temporary-file management, memory usage, media encoding settings, queue behavior, and unnecessary data copies.

## Security

- Never commit `.env` files or credentials.
- Use IAM least-privilege permissions in production.
- Use pre-signed URLs for client uploads.
- Validate filenames and media inputs.
- Use unique object keys.
- Validate media before processing.
- Use secure production credentials and secret management.
- Do not use development credentials in production.
- Run the Docker Celery worker as a non-root user.

## Git Workflow

Use feature branches for development.

Recommended workflow:

1. Create a feature branch.
2. Implement the assigned issue.
3. Add or update tests.
4. Run `pytest`.
5. Push the branch.
6. Open a Pull Request.
7. Review the Pull Request.
8. Ensure CI checks pass.
9. Merge into the integration branch.
10. Run integration tests.


## Deployment

A production deployment should include:

- FastAPI containers
- Celery worker containers
- RabbitMQ or a managed message broker
- Redis or a managed Redis service
- AWS S3
- AWS CloudFront when CDN delivery is required
- Prometheus monitoring
- Secure environment configuration
- Appropriate worker concurrency
- Centralized logging and operational monitoring

The number of Celery workers can be increased according to workload.

## Project Completion Criteria

The project is complete when:

- All assigned implementation issues are finished.
- The full media-processing workflow works end-to-end.
- Automated and integration tests pass.
- Retry and failure behavior is validated.
- Monitoring is operational.
- Docker deployment works.
- Load and performance testing is completed.
- Deployment documentation is finalized.

## Repository

https://github.com/shahanazpr/distributed-media-processing-microservice
