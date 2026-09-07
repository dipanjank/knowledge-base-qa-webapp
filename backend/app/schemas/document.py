import uuid
from datetime import datetime

from sqlmodel import SQLModel


class DocumentInfo(SQLModel):
    id: uuid.UUID
    filename: str


class DocumentUploadResponse(SQLModel):
    job_id: uuid.UUID
    documents: list[DocumentInfo]


class DocumentResponse(SQLModel):
    id: uuid.UUID
    filename: str
    file_type: str
    file_size_bytes: int
    status: str
    text_preview: str | None
    created_at: datetime
    indexed_at: datetime | None


class DocumentListResponse(SQLModel):
    items: list[DocumentResponse]
    total: int
