import os
import uuid
from datetime import datetime, timezone

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7")
os.environ.setdefault("AWS_REGION", "eu-west-1")
os.environ.setdefault("S3_BUCKET_NAME", "test-bucket")
os.environ.setdefault("SQS_QUEUE_URL", "http://localhost:4566/queue/test")
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("ADMIN_EMAIL", "admin@test.local")
os.environ.setdefault("ADMIN_PASSWORD", "testpassword")

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.models.document import Document
from app.models.rag_job import RagJob
from app.models.user import User
from app.utils.auth import hash_password


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)


@pytest_asyncio.fixture
async def async_session():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


def make_document(
    user_id: uuid.UUID | None = None,
    filename: str = "test.txt",
    file_type: str = "txt",
    file_size_bytes: int = 100,
    s3_key: str | None = None,
    status: str = "pending",
) -> Document:
    return Document(
        id=uuid.uuid4(),
        user_id=user_id or uuid.uuid4(),
        filename=filename,
        file_type=file_type,
        file_size_bytes=file_size_bytes,
        s3_key=s3_key or f"{uuid.uuid4()}/{filename}",
        status=status,
        created_at=datetime.now(timezone.utc),
    )


def make_rag_job(
    user_id: uuid.UUID | None = None,
    total_documents: int = 1,
    status: str = "pending",
) -> RagJob:
    return RagJob(
        id=uuid.uuid4(),
        user_id=user_id or uuid.uuid4(),
        status=status,
        total_documents=total_documents,
        created_at=datetime.now(timezone.utc),
    )


def make_user(
    username: str = "alice",
    email: str = "alice@example.com",
    password: str = "testpass123",
    role: str = "user",
) -> User:
    return User(
        id=uuid.uuid4(),
        username=username,
        email=email,
        password_hash=hash_password(password),
        role=role,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
