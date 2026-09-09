import uuid
from datetime import datetime

from sqlmodel import SQLModel


class AskRequest(SQLModel):
    question: str
    conversation_id: uuid.UUID | None = None


class SourceInfo(SQLModel):
    document_id: str
    filename: str
    excerpt: str


class AskResponse(SQLModel):
    answer: str
    sources: list[SourceInfo]
    conversation_id: uuid.UUID


class MessageResponse(SQLModel):
    id: uuid.UUID
    role: str
    content: str
    sources: list[SourceInfo] | None
    created_at: datetime


class ConversationSummary(SQLModel):
    id: uuid.UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(SQLModel):
    items: list[ConversationSummary]
    total: int


class ConversationDetailResponse(SQLModel):
    id: uuid.UUID
    title: str | None
    messages: list[MessageResponse]
