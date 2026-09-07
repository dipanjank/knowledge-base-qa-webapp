import uuid
from asyncio import get_event_loop

from fastapi import HTTPException, UploadFile, status

from app.models.document import Document
from app.models.rag_job import RagJob, RagJobDocument
from app.repositories.document_repository import DocumentRepository
from app.repositories.rag_job_repository import RagJobRepository
from app.schemas.document import (
    DocumentInfo,
    DocumentListResponse,
    DocumentResponse,
    DocumentUploadResponse,
)
from app.schemas.user import MessageResponse
from app.services.s3_service import S3Service
from app.services.sqs_service import SQSService

MAX_FILES = 5
ALLOWED_EXTENSIONS = {"txt"}


class DocumentService:
    def __init__(
        self,
        document_repo: DocumentRepository,
        rag_job_repo: RagJobRepository,
        s3_service: S3Service,
        sqs_service: SQSService,
    ):
        self.document_repo = document_repo
        self.rag_job_repo = rag_job_repo
        self.s3 = s3_service
        self.sqs = sqs_service

    async def upload_documents(
        self, files: list[UploadFile], user_id: uuid.UUID
    ) -> DocumentUploadResponse:
        if len(files) > MAX_FILES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum {MAX_FILES} files per upload",
            )

        active_job = await self.rag_job_repo.get_active_job(user_id)
        if active_job:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A RAG job is already in progress",
            )

        documents: list[Document] = []
        for file in files:
            ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
            if ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported file type: {file.filename}. Only .txt files are allowed.",
                )

            data = await file.read()
            s3_key = f"{user_id}/{uuid.uuid4()}/{file.filename}"

            loop = get_event_loop()
            await loop.run_in_executor(None, self.s3.upload_file, s3_key, data, file.content_type)

            doc = Document(
                user_id=user_id,
                filename=file.filename,
                file_type=ext,
                file_size_bytes=len(data),
                s3_key=s3_key,
                status="pending",
            )
            documents.append(doc)

        # Create RAG job
        job = RagJob(user_id=user_id, total_documents=len(documents))
        job = await self.rag_job_repo.create(job)

        # Create documents and link to job
        for doc in documents:
            doc = await self.document_repo.create(doc)
            await self.rag_job_repo.create_job_document(
                RagJobDocument(rag_job_id=job.id, document_id=doc.id)
            )
        await self.document_repo.session.commit()

        # Send SQS message
        loop = get_event_loop()
        await loop.run_in_executor(
            None, self.sqs.send_message, {"job_id": str(job.id), "user_id": str(user_id)}
        )

        return DocumentUploadResponse(
            job_id=job.id,
            documents=[DocumentInfo(id=d.id, filename=d.filename) for d in documents],
        )

    async def list_documents(self, user_id: uuid.UUID) -> DocumentListResponse:
        docs = await self.document_repo.get_by_user(user_id)
        total = await self.document_repo.count_by_user(user_id)
        return DocumentListResponse(
            items=[
                DocumentResponse(
                    id=d.id,
                    filename=d.filename,
                    file_type=d.file_type,
                    file_size_bytes=d.file_size_bytes,
                    status=d.status,
                    text_preview=d.text_preview,
                    created_at=d.created_at,
                    indexed_at=d.indexed_at,
                )
                for d in docs
            ],
            total=total,
        )

    async def delete_document(self, document_id: uuid.UUID, user_id: uuid.UUID) -> MessageResponse:
        doc = await self.document_repo.get_by_id_and_user(document_id, user_id)
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        await self.document_repo.soft_delete(doc)
        return MessageResponse(message="Document deleted", id=doc.id)
