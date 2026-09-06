import json
import logging
import signal
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import sessionmaker

from app.job_processor import JobProcessor
from app.models.rag_job import RagJob

logger = logging.getLogger(__name__)


class SqsWorker:
    """Polls SQS for RAG job messages and delegates processing to JobProcessor."""

    def __init__(self, queue_url: str, job_processor: JobProcessor, sqs_client, session_factory: sessionmaker):
        self._queue_url = queue_url
        self._job_processor = job_processor
        self._sqs = sqs_client
        self._session_factory = session_factory

    def run(self) -> None:
        """Start the long-polling loop. Blocks until a shutdown signal is received."""
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

        logger.info("RAG worker starting, polling %s", self._queue_url)

        while not self._job_processor.shutdown_requested:
            message = self._poll()
            if message is None:
                continue

            body = json.loads(message["Body"])
            job_id = uuid.UUID(body["job_id"])
            receipt_handle = message["ReceiptHandle"]

            logger.info("Received job %s", job_id)

            try:
                self._job_processor.process(job_id)
                self._delete_message(receipt_handle)
                logger.info("Job %s completed, SQS message deleted", job_id)
            except Exception:
                logger.exception("Fatal error processing job %s, message NOT deleted", job_id)
                with self._session_factory() as session:
                    job_row = session.get(RagJob, job_id)
                    if job_row and job_row.status == "processing":
                        job_row.status = "failure"
                        job_row.completed_at = datetime.now(timezone.utc)
                        session.commit()

        logger.info("RAG worker shutting down")

    def _poll(self) -> dict | None:
        response = self._sqs.receive_message(
            QueueUrl=self._queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20,
            VisibilityTimeout=900,
        )
        messages = response.get("Messages", [])
        return messages[0] if messages else None

    def _delete_message(self, receipt_handle: str) -> None:
        self._sqs.delete_message(QueueUrl=self._queue_url, ReceiptHandle=receipt_handle)

    def _handle_signal(self, signum, frame):
        logger.info("Shutdown signal received, finishing current work...")
        self._job_processor.shutdown_requested = True
