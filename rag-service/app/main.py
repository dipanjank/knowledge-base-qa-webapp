import logging

import boto3
from langchain_aws import BedrockEmbeddings
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.document_processor import DocumentProcessor
from app.job_processor import JobProcessor
from app.services.s3_service import S3Service
from app.sqs_worker import SqsWorker


def create_worker() -> SqsWorker:
    """Wire all dependencies and return a ready-to-run SqsWorker."""
    settings = Settings()

    engine = create_engine(settings.database_url)
    session_factory = sessionmaker(engine, expire_on_commit=False)

    s3 = S3Service(bucket=settings.s3_bucket_name, region=settings.aws_region)

    embeddings = BedrockEmbeddings(
        model_id=settings.bedrock_embedding_model_id,
        region_name=settings.aws_region,
    )

    # Splits on natural text boundaries (paragraphs, lines, words) with
    # token-based length measurement via tiktoken cl100k_base encoding.
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=500,
        chunk_overlap=50,
    )

    vector_store = PGVector(
        embeddings=embeddings,
        collection_name="document_chunks",
        connection=settings.database_url,
        use_jsonb=True,
    )

    document_processor = DocumentProcessor(s3, text_splitter, vector_store, session_factory)
    job_processor = JobProcessor(document_processor, session_factory)
    sqs_client = boto3.client("sqs", region_name=settings.aws_region)

    return SqsWorker(settings.sqs_queue_url, job_processor, sqs_client, session_factory)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    worker = create_worker()
    worker.run()
