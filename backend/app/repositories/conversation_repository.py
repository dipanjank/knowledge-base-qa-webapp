import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.models.conversation import Conversation, Message
from app.repositories.base import GenericRepository


class ConversationRepository(GenericRepository[Conversation]):
    """Async repository for conversations and their messages."""

    def __init__(self, session: AsyncSession):
        super().__init__(Conversation, session)

    async def get_by_id_and_user(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> Conversation | None:
        stmt = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_recent_by_user(self, user_id: uuid.UUID, limit: int = 10) -> list[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_user(self, user_id: uuid.UUID) -> int:
        stmt = select(func.count(Conversation.id)).where(Conversation.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar()

    async def get_messages(self, conversation_id: uuid.UUID) -> list[Message]:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add_message(self, message: Message) -> Message:
        self.session.add(message)
        await self.session.flush()
        return message

    async def update_timestamp(self, conversation: Conversation) -> None:
        conversation.updated_at = func.now()
        self.session.add(conversation)
        await self.session.flush()
