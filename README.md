# distributed-media-processing-microservice
Event-driven media processing microservice using FastAPI, Celery, RabbitMQ, Redis, Pillow, FFmpeg, and AWS S3/CloudFront.
## S3 Storage Testing

The S3 storage layer is tested using `pytest` with mocked S3 client operations.

The tests cover:

- Successful file upload
- Upload failures
- Successful file download
- Download failures
- Missing S3 objects
- Missing S3 bucket configuration

The tests do not require a real AWS account, S3 bucket, or AWS credentials because S3 operations are mocked during testing.

### Running S3 Tests

From the project root, run:

```bash
python -m pytest -v tests/test_s3_storage.py