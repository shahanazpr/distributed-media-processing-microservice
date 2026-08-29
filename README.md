# distributed-media-processing-microservice
Event-driven media processing microservice using FastAPI, Celery, RabbitMQ, Redis, Pillow, FFmpeg, and AWS S3/CloudFront.

## Environment Setup

1. Copy `.env.example` to `.env`
2. Fill in your local AWS, Redis, and RabbitMQ credentials
3. Never commit `.env` — it's gitignored

| Variable | Description | Default |
|---|---|---|
| APP_ENV | development/production | development |
| AWS_ACCESS_KEY_ID | AWS IAM access key | — |
| AWS_SECRET_ACCESS_KEY | AWS IAM secret key | — |
| S3_INPUT_BUCKET | Bucket for raw uploads | — |
| S3_OUTPUT_BUCKET | Bucket for processed media | — |
| REDIS_HOST | Redis server host | localhost |
| RABBITMQ_HOST | RabbitMQ server host | localhost |