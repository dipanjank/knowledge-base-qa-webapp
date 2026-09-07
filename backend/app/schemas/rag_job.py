import uuid
from datetime import datetime

from sqlmodel import SQLModel


class RagJobDocumentStatus(SQLModel):
    id: uuid.UUID
    filename: str
    status: str
    error_message: str | None


class RagJobResponse(SQLModel):
    id: uuid.UUID
    status: str
    total_documents: int
    documents_processed: int
    documents_failed: int
    documents: list[RagJobDocumentStatus]
    created_at: datetime
    completed_at: datetime | None


class RagJobListResponse(SQLModel):
    items: list[RagJobResponse]
    total: int
