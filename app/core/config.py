from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # --- Application ---
    app_name: str = "Media Processing Microservice"
    app_env: str = "development"
    debug: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # --- AWS / S3 ---
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "ap-south-1"
    s3_input_bucket: str = ""
    s3_output_bucket: str = ""
    # Leave blank to use real AWS; set this if using a local S3 stand-in (e.g. MinIO)
    s3_endpoint_url: str = ""

    # --- Redis ---
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    # --- RabbitMQ ---
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"
    rabbitmq_vhost: str = "/"

    @property
    def redis_url(self) -> str:
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def rabbitmq_url(self) -> str:
        return (
            f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}"
            f"@{self.rabbitmq_host}:{self.rabbitmq_port}{self.rabbitmq_vhost}"
        )


@lru_cache()
def get_settings() -> Settings:
    return Settings()