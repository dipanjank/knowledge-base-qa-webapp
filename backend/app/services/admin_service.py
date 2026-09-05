from fastapi import HTTPException, status

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    CreateUserRequest,
    CreateUserResponse,
    MessageResponse,
    UserListResponse,
    UserResponse,
)
from app.utils.auth import generate_password, hash_password


class AdminService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def create_user(self, body: CreateUserRequest) -> CreateUserResponse:
        existing = await self.user_repo.get_by_username_or_email(body.username, body.email)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username or email already exists",
            )

        password = generate_password()
        user = await self.user_repo.create(
            User(
                username=body.username,
                email=body.email,
                password_hash=hash_password(password),
            )
        )

        return CreateUserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            password=password,
            created_at=user.created_at,
        )

    async def list_users(self) -> UserListResponse:
        users = await self.user_repo.get_all(order_by="created_at")
        total = await self.user_repo.count()
        return UserListResponse(
            items=[
                UserResponse(
                    id=u.id,
                    username=u.username,
                    email=u.email,
                    role=u.role,
                    created_at=u.created_at,
                )
                for u in users
            ],
            total=total,
        )

    async def delete_user(self, user_id: str) -> MessageResponse:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        if user.role == "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete admin users",
            )

        await self.user_repo.delete(user)
        return MessageResponse(message="User deleted", id=user.id)
