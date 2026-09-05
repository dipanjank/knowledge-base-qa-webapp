import uuid
from datetime import datetime

from pydantic import EmailStr
from sqlmodel import SQLModel


class CreateUserRequest(SQLModel):
    username: str
    email: EmailStr


class CreateUserResponse(SQLModel):
    id: uuid.UUID
    username: str
    email: str
    password: str
    created_at: datetime


class UserResponse(SQLModel):
    id: uuid.UUID
    username: str
    email: str
    role: str
    created_at: datetime


class UserListResponse(SQLModel):
    items: list[UserResponse]
    total: int


class MessageResponse(SQLModel):
    message: str
    id: uuid.UUID | None = None
