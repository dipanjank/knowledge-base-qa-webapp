import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.models.document import Document
from app.models.rag_job import RagJob, RagJobDocument
from app.repositories.base import GenericRepository


class RagJobRepository(GenericRepository[RagJob]):
    def __init__(self, session: AsyncSession):
        super().__init__(RagJob, session)

    async def get_active_job(self, user_id: uuid.UUID) -> RagJob | None:
        stmt = select(RagJob).where(
            RagJob.user_id == user_id,
            RagJob.status.in_(["pending", "processing"]),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_jobs(self, user_id: uuid.UUID) -> list[RagJob]:
        stmt = (
            select(RagJob)
            .where(RagJob.user_id == user_id)
            .order_by(RagJob.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_user_jobs(self, user_id: uuid.UUID) -> int:
        stmt = select(func.count(RagJob.id)).where(RagJob.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar()

    async def get_job_documents(self, job_id: uuid.UUID) -> list[tuple[RagJobDocument, str]]:
        """Return job documents with their filenames."""
        stmt = (
            select(RagJobDocument, Document.filename)
            .join(Document, RagJobDocument.document_id == Document.id)
            .where(RagJobDocument.rag_job_id == job_id)
        )
        result = await self.session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def create_job_document(self, job_doc: RagJobDocument) -> RagJobDocument:
        self.session.add(job_doc)
        await self.session.flush()
        return job_doc
