import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user, get_qa_service
from app.models.user import User
from app.schemas.qa import (
    AskRequest,
    AskResponse,
    ConversationDetailResponse,
    ConversationListResponse,
)
from app.services.qa_service import QAService

router = APIRouter(prefix="/api/qa", tags=["qa"])


@router.post("/ask", response_model=AskResponse)
async def ask(
    body: AskRequest,
    user: User = Depends(get_current_user),
    service: QAService = Depends(get_qa_service),
):
    try:
        return await service.ask(user.id, body.question, body.conversation_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    user: User = Depends(get_current_user),
    service: QAService = Depends(get_qa_service),
):
    return await service.list_conversations(user.id)


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    service: QAService = Depends(get_qa_service),
):
    result = await service.get_conversation(user.id, conversation_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return result
