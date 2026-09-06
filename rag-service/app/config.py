from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Worker configuration loaded from environment variables."""

    database_url: str
    aws_region: str
    s3_bucket_name: str
    sqs_queue_url: str
    bedrock_embedding_model_id: str

    model_config = {"env_prefix": "", "case_sensitive": False}
