# RAG Service

Asynchronous document ingestion worker for the Knowledge Base QA application. Polls an SQS queue for RAG job messages, downloads documents from S3, splits and embeds the text using LangChain, and stores vectors in PostgreSQL via pgvector.

## How It Works

1. Backend creates a RAG job and sends an SQS message with the `job_id`
2. Worker picks up the message via long-polling (20s wait, 900s visibility timeout)
3. For each document in the job:
   - Downloads the file from S3
   - Splits text into chunks (500 tokens, 50 overlap) using `RecursiveCharacterTextSplitter` with tiktoken
   - Embeds chunks via Amazon Titan V2 (Bedrock) using `BedrockEmbeddings`
   - Stores vectors in PostgreSQL using LangChain's `PGVector` with JSONB metadata
   - Updates document status to `ready` or `failed`
4. Sets final job status: `success`, `partial_success`, or `failure`
5. Deletes the SQS message on success; leaves it for retry on fatal errors (DLQ after 3 attempts)

Per-document errors are isolated — a single failed document does not block the rest of the job. Graceful shutdown on SIGTERM/SIGINT finishes the current document before exiting.

## Architecture

```
SQS Queue
   │
   ▼
SqsWorker          Polls SQS, parses job_id, handles signals
   │
   ▼
JobProcessor       Iterates documents in a job, tracks per-doc and job-level status
   │
   ▼
DocumentProcessor  Downloads from S3, splits text, embeds via LangChain, stores vectors
```

All dependencies are wired in `app/main.py:create_worker()` and injected via constructors — no module-level state.

## Environment Variables

| Variable                     | Description                                                           |
|------------------------------|-----------------------------------------------------------------------|
| `DATABASE_URL`               | PostgreSQL connection string (`postgresql://...`)                     |
| `AWS_REGION`                 | AWS region for S3, SQS, and Bedrock                                   |
| `S3_BUCKET_NAME`             | S3 bucket containing uploaded documents                               |
| `SQS_QUEUE_URL`              | SQS queue URL for RAG job messages                                    |
| `BEDROCK_EMBEDDING_MODEL_ID` | Bedrock model ID for embeddings (e.g. `amazon.titan-embed-text-v2:0`) |

## Development

```bash
cd rag-service
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**Run locally** (requires environment variables and a running PostgreSQL + localstack):

```bash
python -m app.main
```

**Lint:**

```bash
ruff check app/
```

**Test:**

```bash
pytest -v
```

## Docker

```bash
docker build -t kbqa-rag .
docker run --env-file .env kbqa-rag
```

## Deployment

Runs as an ECS Fargate service (no load balancer — worker only). The task role requires:
- SQS: `ReceiveMessage`, `DeleteMessage`, `GetQueueAttributes`
- S3: `GetObject`
- Bedrock: `InvokeModel`
