from fastapi import APIRouter, Depends, UploadFile, status

from app.dependencies import get_current_user, get_document_service
from app.models.user import User
from app.schemas.document import DocumentListResponse, DocumentUploadResponse
from app.schemas.user import MessageResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_documents(
    files: list[UploadFile],
    user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    return await service.upload_documents(files, user.id)


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    return await service.list_documents(user.id)


@router.delete("/{document_id}", response_model=MessageResponse)
async def delete_document(
    document_id: str,
    user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    return await service.delete_document(document_id, user.id)
