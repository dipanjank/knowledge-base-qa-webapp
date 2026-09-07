import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, func
from sqlmodel import Field, SQLModel


class RagJob(SQLModel, table=True):
    __tablename__ = "rag_jobs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(nullable=False)
    status: str = Field(default="pending", sa_column=Column(String(20), nullable=False, server_default="pending"))
    total_documents: int = Field(sa_column=Column(Integer, nullable=False))
    documents_processed: int = Field(default=0, sa_column=Column(Integer, nullable=False, server_default="0"))
    documents_failed: int = Field(default=0, sa_column=Column(Integer, nullable=False, server_default="0"))
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()))
    completed_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))


class RagJobDocument(SQLModel, table=True):
    __tablename__ = "rag_job_documents"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    rag_job_id: uuid.UUID = Field(nullable=False)
    document_id: uuid.UUID = Field(nullable=False)
    status: str = Field(default="pending", sa_column=Column(String(20), nullable=False, server_default="pending"))
    error_message: str | None = None
    started_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    completed_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
