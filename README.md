Distributed Media Processing Microservice

An event-driven backend microservice for handling heavy, asynchronous
media-processing workloads.

Project Overview

This microservice offloads CPU-intensive media-processing operations
from the primary web application. Clients submit jobs through FastAPI,
media is stored in S3, and processing is performed asynchronously by
Celery workers through RabbitMQ. Redis tracks job status, while
processed assets are stored in S3 and delivered through CloudFront.

Architecture

Client / Main Web Application | v FastAPI | +—-+—————-+ | | v v Redis
Pre-signed S3 URL Job Status | v S3 | v RabbitMQ | v Celery Workers |
+———+———+ | | v v Pillow FFmpeg Images Videos | | +———+———+ | v
Watermark | v S3 Output | v CloudFront CDN | v Client

Prometheus monitors application, queue, worker, processing, and resource
metrics.

Key Features

-   FastAPI REST API for job submission and status tracking
-   Pre-signed S3 upload URLs
-   Redis-backed job status tracking
-   RabbitMQ message broker
-   Celery asynchronous workers
-   Pillow image processing
-   FFmpeg video processing
-   Image crop, resize, compression, and watermarking
-   Video thumbnail extraction and MP4/H.264 transcoding
-   Video watermarking
-   S3 input and output storage
-   CloudFront CDN delivery
-   Retry and failure handling
-   Multiple Celery workers
-   Docker Compose deployment
-   Prometheus monitoring
-   Pytest automated testing
-   GitHub Actions CI
-   Load and performance testing

Technology Stack

Programming Language: Python API Framework: FastAPI Task Queue: Celery
Message Broker: RabbitMQ Job Status / Cache: Redis Image Processing:
Pillow Video Processing: FFmpeg / FFmpeg-python Cloud Storage: AWS S3
AWS SDK: Boto3 CDN: AWS CloudFront Containerization: Docker / Docker
Compose Monitoring: Prometheus Testing: Pytest CI: GitHub Actions

End-to-End Workflow

1.  Client requests a processing job.
2.  FastAPI validates the request and creates a unique job ID.
3.  FastAPI generates a pre-signed S3 upload URL.
4.  Client uploads the original media directly to S3.
5.  The processing task is sent to Celery through RabbitMQ.
6.  Redis records the job as PENDING.
7.  A Celery worker receives the task.
8.  The worker changes the job to PROCESSING.
9.  The worker downloads the input media from S3.
10. Pillow or FFmpeg processes the media.
11. Watermarking is applied when configured.
12. Processed files are uploaded to S3.
13. Redis is updated with COMPLETED or FAILED status.
14. The job result contains processed output information and, when
    configured, a CloudFront URL.
15. The client retrieves the result through the job-status API.

Job States

PENDING PROCESSING COMPLETED FAILED

Failure flow:

PENDING -> PROCESSING -> RETRY -> PROCESSING -> FAILED

Transient failures are retried according to the configured Celery retry
policy.

API

Health Check

GET /health

Example response:

{ “status”: “healthy”, “service”: “media-processing-microservice” }

Create Processing Job

POST /jobs

Example request:

{ “filename”: “image.jpg”, “operation”: “resize” }

The endpoint returns a job ID and pre-signed S3 upload URL. The final
response fields depend on the implemented processing configuration.

Get Job Status

GET /jobs/{job_id}

The response contains the current status and, after successful
processing, output information such as S3 object keys and CloudFront
URLs.

API Documentation

When running locally:

http://127.0.0.1:8000/docs http://127.0.0.1:8000/openapi.json

Image Processing

Pillow is used for:

-   Cropping
-   Resizing
-   Compression
-   JPEG output generation
-   Watermarking

Video Processing

FFmpeg is used for:

-   Thumbnail extraction
-   Video transcoding
-   MP4 output
-   H.264 encoding
-   Video optimization
-   Watermarking

Storage

AWS S3 is used for original and processed media.

Example object layout:

uploads//original-file.jpg outputs//processed-file.jpg
outputs//optimized.mp4 outputs//thumbnail.jpg

The storage service supports uploads, downloads, object existence
checks, and pre-signed upload URL generation.

Never hardcode or commit AWS credentials.

CloudFront CDN

Processed media is stored in S3 and delivered through CloudFront.

S3 Output -> CloudFront -> Client

The completed job can return a CDN URL for the processed asset when
CloudFront is configured.

Asynchronous Processing

Celery executes processing outside the FastAPI request-response cycle.

RabbitMQ distributes tasks to workers.

Multiple workers can be started to process jobs concurrently.

Example local worker command:

celery -A app.tasks.celery_app.celery_app worker –loglevel=info
–pool=solo

Error Handling and Retries

The system handles:

-   S3 connection and transfer failures
-   Missing S3 objects
-   Network timeouts
-   Invalid media
-   Corrupted images or videos
-   Pillow failures
-   FFmpeg failures
-   RabbitMQ/Celery failures
-   Worker failures

Transient failures are retried. Jobs that exceed the configured retry
limit are marked FAILED and the error is stored.

Monitoring

Prometheus provides operational metrics such as:

-   Total jobs
-   Completed jobs
-   Failed jobs
-   Processing duration
-   Queue activity
-   Worker activity
-   CPU usage
-   Memory usage

Metrics endpoint:

GET /metrics

Docker Compose

The final containerized environment includes:

-   FastAPI
-   Celery worker
-   RabbitMQ
-   Redis
-   Prometheus

An S3-compatible service such as MinIO may be used for local development
and integration testing.

Start:

docker compose up –build

Stop:

docker compose down

Check services:

docker compose ps

View logs:

docker compose logs -f

Local Development

Clone:

git clone
https://github.com/shahanazpr/distributed-media-processing-microservice.git
cd distributed-media-processing-microservice

Create a virtual environment on Windows:

python -m venv .venv .venv.ps1

Linux/macOS:

python3 -m venv .venv source .venv/bin/activate

Install dependencies:

pip install -r requirements.txt

Configure environment variables using .env.example.

Never commit .env or real credentials.

Environment Variables

The final .env.example should document every variable actually used by
the implementation.

Typical configuration includes:

APP_ENV AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_REGION
S3_BUCKET_NAME or input/output bucket variables S3_ENDPOINT_URL for
local S3-compatible storage REDIS_URL or Redis host/port variables
CELERY_BROKER_URL RABBITMQ_HOST RABBITMQ_PORT CLOUDFRONT_DOMAIN
PROMETHEUS_PORT

Use the exact variable names implemented in the final code.

Running the Application

FastAPI:

uvicorn app.main:app –reload

Application:

http://127.0.0.1:8000

API documentation:

http://127.0.0.1:8000/docs

Celery:

celery -A app.tasks.celery_app.celery_app worker –loglevel=info
–pool=solo

Testing

Run all tests:

pytest

Verbose:

pytest -v

Testing should cover:

-   FastAPI endpoints
-   Job creation and status retrieval
-   Redis job storage
-   S3 operations
-   Pre-signed URLs
-   Pillow processing
-   FFmpeg processing
-   Watermarking
-   Celery tasks
-   Retry and failure behavior
-   S3 input/output workflow
-   End-to-end processing

Continuous Integration

GitHub Actions runs automated validation on pushes and pull requests.

The CI workflow should install dependencies and run the automated test
suite. Pull requests should be reviewed and merged only after required
checks pass.

Load Testing and Performance

The final system should be tested with:

-   Multiple simultaneous job submissions
-   Multiple image jobs
-   Multiple video jobs
-   Mixed image/video workloads
-   Multiple Celery workers
-   Failed jobs
-   Retry scenarios
-   Queue behavior under load
-   S3 operations under load

Measure:

-   API response time
-   Queue waiting time
-   Job processing time
-   Worker CPU usage
-   Memory usage
-   S3 download/upload time
-   Image processing time
-   Video processing time

Performance optimization should focus on worker concurrency,
temporary-file management, memory usage, media encoding settings, queue
behavior, and unnecessary data copies.

Security

-   Never commit .env files or credentials.
-   Use IAM least-privilege permissions.
-   Use pre-signed URLs for client uploads.
-   Validate filenames and media inputs.
-   Use unique object keys.
-   Validate media before processing.
-   Use secure production credentials and secret management.
-   Do not use development credentials in production.

Git Workflow

Use feature branches for development.

Recommended workflow:

1.  Create a feature branch.
2.  Implement the assigned issue.
3.  Add or update tests.
4.  Run pytest.
5.  Push the branch.
6.  Open a Pull Request.
7.  Review the Pull Request.
8.  Ensure CI checks pass.
9.  Merge into the integration branch.
10. Run integration tests.

Final Validation Checklist

[ ] FastAPI starts successfully [ ] Health endpoint works [ ] Job
creation works [ ] Pre-signed S3 upload works [ ] Redis job status works
[ ] RabbitMQ receives tasks [ ] Celery workers process tasks [ ] Pillow
processes images [ ] Images can be cropped, resized, and compressed [ ]
FFmpeg processes videos [ ] Video thumbnails are generated [ ] Videos
are transcoded to MP4/H.264 [ ] Image watermarking works [ ] Video
watermarking works [ ] Outputs are uploaded to S3 [ ] CloudFront
delivers processed assets [ ] Job statuses transition correctly [ ]
Retry behavior works [ ] Failed jobs are recorded [ ] Multiple workers
process jobs concurrently [ ] Prometheus metrics are available [ ]
Docker Compose starts the system [ ] Automated tests pass [ ] GitHub
Actions CI passes [ ] Load testing is completed [ ] Memory usage is
reviewed [ ] Performance bottlenecks are addressed [ ] Deployment
documentation is complete [ ] Troubleshooting documentation is complete
[ ] Final end-to-end demonstration succeeds

Deployment

The production deployment should include:

-   FastAPI containers
-   Celery worker containers
-   RabbitMQ or a managed message broker
-   Redis or a managed Redis service
-   AWS S3
-   AWS CloudFront
-   Prometheus monitoring
-   Secure environment configuration
-   Appropriate worker concurrency
-   Centralized logging and operational monitoring

The number of Celery workers can be increased according to workload.

Project Completion Criteria

The project is complete when all assigned implementation issues are
finished, the full media-processing workflow works end-to-end, automated
and integration tests pass, retries and failures are validated,
monitoring is operational, Docker deployment works, load/performance
testing is completed, and deployment documentation is finalized.

Repository

https://github.com/shahanazpr/distributed-media-processing-microservice
