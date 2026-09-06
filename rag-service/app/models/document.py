import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel


class Document(SQLModel, table=True):
    __tablename__ = "documents"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(nullable=False)
    filename: str = Field(max_length=255)
    file_type: str = Field(max_length=10)
    file_size_bytes: int
    s3_key: str = Field(max_length=512)
    status: str = Field(default="pending", max_length=20)
    text_preview: str | None = None
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()))
    indexed_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    deleted_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
