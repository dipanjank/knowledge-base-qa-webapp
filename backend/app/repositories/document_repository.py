import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.models.document import Document
from app.repositories.base import GenericRepository

logger = logging.getLogger(__name__)


class DocumentRepository(GenericRepository[Document]):
    def __init__(self, session: AsyncSession):
        super().__init__(Document, session)

    async def get_by_user(self, user_id: uuid.UUID) -> list[Document]:
        stmt = (
            select(Document)
            .where(Document.user_id == user_id, Document.deleted_at.is_(None))
            .order_by(Document.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_user(self, user_id: uuid.UUID) -> int:
        stmt = select(func.count(Document.id)).where(
            Document.user_id == user_id, Document.deleted_at.is_(None)
        )
        result = await self.session.execute(stmt)
        return result.scalar()

    async def get_by_id_and_user(self, document_id: uuid.UUID, user_id: uuid.UUID) -> Document | None:
        stmt = select(Document).where(
            Document.id == document_id,
            Document.user_id == user_id,
            Document.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def soft_delete(self, document: Document) -> None:
        document.deleted_at = datetime.now(timezone.utc)
        self.session.add(document)
        try:
            await self.session.execute(
                text("DELETE FROM langchain_pg_embedding WHERE cmetadata->>'document_id' = :doc_id"),
                {"doc_id": str(document.id)},
            )
        except (OperationalError, ProgrammingError):
            logger.debug("langchain_pg_embedding table not found, skipping embedding cleanup")
        await self.session.commit()
