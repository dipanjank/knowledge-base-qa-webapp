from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://kbqa:kbqa@localhost:5432/kbqa"
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    aws_region: str = "us-east-1"
    s3_bucket_name: str = "kbqa-documents"
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    bedrock_embedding_model_id: str = "amazon.titan-embed-text-v2:0"

    admin_username: str = "admin"
    admin_email: str = "admin@example.com"
    admin_password: str = "admin"

    cors_origins: str = "http://localhost:5173"

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()
