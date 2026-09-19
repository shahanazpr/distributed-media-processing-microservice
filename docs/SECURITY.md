# Security Configuration

- Store credentials in environment variables.
- Never commit real AWS, RabbitMQ, or Redis credentials.
- RabbitMQ and Redis ports are not exposed to the host.
- Only API port 8000 is exposed.
- DEBUG is disabled by default.
- API errors return generic internal error messages.
- S3 presigned URLs use limited expiration.
- Configure CloudFront through environment variables.
- Run `python -m pytest tests -q` before deployment.
