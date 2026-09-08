import redis
from app.core.config import get_settings

_redis_client = None


def get_redis_client() -> redis.Redis:
    """Returns a singleton Redis client built from app settings."""
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password or None,
            decode_responses=True,
        )
    return _redis_client