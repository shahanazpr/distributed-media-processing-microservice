from app.core.config import get_settings
from app.storage.s3 import S3Storage


class CDNConfigError(Exception):
    """Raised when CloudFront is not configured but a CDN URL is requested."""
    pass


def build_cdn_url(object_key: str) -> str:
    """Build a CloudFront URL for an object stored in S3."""
    settings = get_settings()
    if not settings.cloudfront_domain:
        raise CDNConfigError("CLOUDFRONT_DOMAIN is not configured")

    object_key = object_key.lstrip("/")
    return f"https://{settings.cloudfront_domain}/{object_key}"


def get_output_cdn_info(object_key: str, storage: S3Storage = None) -> dict:
    """
    Build CDN output info for a processed media object.
    Checks the object actually exists in S3 before returning a CDN URL.
    """
    storage = storage or S3Storage()

    if not storage.object_exists(object_key):
        return {
            "s3_key": object_key,
            "cdn_url": None,
            "error": "Output object not found in S3",
        }

    try:
        cdn_url = build_cdn_url(object_key)
    except CDNConfigError:
        cdn_url = None

    return {"s3_key": object_key, "cdn_url": cdn_url}
