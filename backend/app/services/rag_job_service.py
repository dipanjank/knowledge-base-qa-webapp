import uuid

from app.repositories.rag_job_repository import RagJobRepository
from app.schemas.rag_job import RagJobDocumentStatus, RagJobListResponse, RagJobResponse


class RagJobService:
    def __init__(self, rag_job_repo: RagJobRepository):
        self.rag_job_repo = rag_job_repo

    async def get_active_job(self, user_id: uuid.UUID) -> RagJobResponse | None:
        job = await self.rag_job_repo.get_active_job(user_id)
        if not job:
            return None
        return await self._to_response(job)

    async def list_jobs(self, user_id: uuid.UUID) -> RagJobListResponse:
        jobs = await self.rag_job_repo.get_user_jobs(user_id)
        total = await self.rag_job_repo.count_user_jobs(user_id)
        items = [await self._to_response(job) for job in jobs]
        return RagJobListResponse(items=items, total=total)

    async def _to_response(self, job) -> RagJobResponse:
        job_docs = await self.rag_job_repo.get_job_documents(job.id)
        return RagJobResponse(
            id=job.id,
            status=job.status,
            total_documents=job.total_documents,
            documents_processed=job.documents_processed,
            documents_failed=job.documents_failed,
            documents=[
                RagJobDocumentStatus(
                    id=jd.document_id,
                    filename=filename,
                    status=jd.status,
                    error_message=jd.error_message,
                )
                for jd, filename in job_docs
            ],
            created_at=job.created_at,
            completed_at=job.completed_at,
        )
