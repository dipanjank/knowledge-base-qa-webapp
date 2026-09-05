from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    jwt_access_token_expire_minutes: int
    jwt_refresh_token_expire_days: int

    aws_region: str
    s3_bucket_name: str
    bedrock_model_id: str
    bedrock_embedding_model_id: str

    admin_username: str
    admin_email: str
    admin_password: str

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()
