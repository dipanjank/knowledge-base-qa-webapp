from fastapi import APIRouter, Depends, status

from app.dependencies import get_admin_service, require_admin
from app.schemas.user import (
    CreateUserRequest,
    CreateUserResponse,
    MessageResponse,
    UserListResponse,
)
from app.services.admin_service import AdminService

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.post("/users", response_model=CreateUserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: CreateUserRequest,
    service: AdminService = Depends(get_admin_service),
):
    return await service.create_user(body)


@router.get("/users", response_model=UserListResponse)
async def list_users(service: AdminService = Depends(get_admin_service)):
    return await service.list_users()


@router.delete("/users/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: str,
    service: AdminService = Depends(get_admin_service),
):
    return await service.delete_user(user_id)
