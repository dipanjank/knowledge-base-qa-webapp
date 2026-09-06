import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import sessionmaker
from sqlmodel import select

from app.document_processor import DocumentProcessor
from app.models.document import Document
from app.models.rag_job import RagJob, RagJobDocument

logger = logging.getLogger(__name__)


class JobProcessor:
    """Processes all documents in a RAG job, tracking per-document and job-level status."""

    def __init__(self, document_processor: DocumentProcessor, session_factory: sessionmaker):
        self._document_processor = document_processor
        self._session_factory = session_factory
        self.shutdown_requested = False

    def process(self, job_id: uuid.UUID) -> None:
        """Process each document in the job. Failures are isolated per document."""
        with self._session_factory() as session:
            job = session.get(RagJob, job_id)
            if not job:
                logger.error("Job %s not found", job_id)
                return

            job.status = "processing"
            session.commit()

            stmt = select(RagJobDocument).where(RagJobDocument.rag_job_id == job_id)
            job_docs = list(session.execute(stmt).scalars().all())

        for job_doc in job_docs:
            if self.shutdown_requested:
                logger.info("Shutdown requested, stopping after current document")
                return

            with self._session_factory() as session:
                job_doc_row = session.get(RagJobDocument, job_doc.id)
                job_doc_row.status = "processing"
                job_doc_row.started_at = datetime.now(timezone.utc)
                session.commit()

                document = session.get(Document, job_doc.document_id)

            try:
                self._document_processor.process(document)

                with self._session_factory() as session:
                    job_doc_row = session.get(RagJobDocument, job_doc.id)
                    job_doc_row.status = "ready"
                    job_doc_row.completed_at = datetime.now(timezone.utc)

                    job_row = session.get(RagJob, job_id)
                    job_row.documents_processed += 1
                    session.commit()

            except Exception as exc:
                logger.exception("Failed to process document %s", document.filename)

                with self._session_factory() as session:
                    job_doc_row = session.get(RagJobDocument, job_doc.id)
                    job_doc_row.status = "failed"
                    job_doc_row.error_message = str(exc)
                    job_doc_row.completed_at = datetime.now(timezone.utc)

                    doc_row = session.get(Document, job_doc.document_id)
                    doc_row.status = "failed"

                    job_row = session.get(RagJob, job_id)
                    job_row.documents_processed += 1
                    job_row.documents_failed += 1
                    session.commit()

        with self._session_factory() as session:
            job_row = session.get(RagJob, job_id)
            if job_row.documents_failed == 0:
                job_row.status = "success"
            elif job_row.documents_failed == job_row.total_documents:
                job_row.status = "failure"
            else:
                job_row.status = "partial_success"
            job_row.completed_at = datetime.now(timezone.utc)
            session.commit()

        logger.info("Job %s finished with status %s", job_id, job_row.status)
