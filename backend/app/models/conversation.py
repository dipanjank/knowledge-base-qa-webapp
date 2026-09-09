import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text, func
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel


class Conversation(SQLModel, table=True):
    """A user's chat session, containing one or more question-answer turns."""

    __tablename__ = "conversations"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(nullable=False)
    title: str | None = Field(default=None, sa_column=Column(String(200)))
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()))
    updated_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()))


class Message(SQLModel, table=True):
    """A single human or AI message within a conversation, optionally carrying source citations."""

    __tablename__ = "messages"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    conversation_id: uuid.UUID = Field(nullable=False)
    role: str = Field(sa_column=Column(String(10), nullable=False))
    content: str = Field(sa_column=Column(Text, nullable=False))
    sources: list | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()))
