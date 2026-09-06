import logging
from datetime import datetime, timezone

from langchain_core.documents import Document as LCDocument
from langchain_postgres import PGVector
from langchain_text_splitters import TextSplitter
from sqlalchemy.orm import sessionmaker

from app.models.document import Document
from app.services.s3_service import S3Service

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Downloads a document from S3, splits and embeds the text, and stores the vectors."""

    def __init__(self, s3: S3Service, text_splitter: TextSplitter, vector_store: PGVector, session_factory: sessionmaker):
        self._s3 = s3
        self._splitter = text_splitter
        self._vector_store = vector_store
        self._session_factory = session_factory

    def process(self, document: Document) -> None:
        """Run the full ingestion pipeline for a single document."""
        data = self._s3.download_file(document.s3_key)
        text = data.decode("utf-8")

        metadata = {
            "document_id": str(document.id),
            "user_id": str(document.user_id),
            "filename": document.filename,
        }
        lc_docs = self._splitter.split_documents([LCDocument(page_content=text, metadata=metadata)])

        if not lc_docs:
            raise ValueError("No text chunks produced from document")

        self._vector_store.add_documents(lc_docs)

        with self._session_factory() as session:
            document_row = session.get(Document, document.id)
            document_row.text_preview = text[:500]
            document_row.status = "ready"
            document_row.indexed_at = datetime.now(timezone.utc)
            session.commit()

        logger.info("Document %s processed: %d chunks", document.filename, len(lc_docs))
