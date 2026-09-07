import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, func
from sqlmodel import Field, SQLModel


class Document(SQLModel, table=True):
    __tablename__ = "documents"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(nullable=False)
    filename: str = Field(sa_column=Column(String(255), nullable=False))
    file_type: str = Field(sa_column=Column(String(10), nullable=False))
    file_size_bytes: int = Field(sa_column=Column(Integer, nullable=False))
    s3_key: str = Field(sa_column=Column(String(512), nullable=False, unique=True))
    status: str = Field(default="pending", sa_column=Column(String(20), nullable=False, server_default="pending"))
    text_preview: str | None = None
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()))
    indexed_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    deleted_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
