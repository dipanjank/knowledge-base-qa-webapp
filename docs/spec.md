# Knowledge Base QA Web Application — System Specification

## 1. Overview

A fullstack web application that allows users to upload TXT documents, chunk and embed them using Amazon Bedrock Titan Embeddings, store vectors in PostgreSQL with pgvector, and perform RAG-based question answering against the indexed content. Document processing (text extraction, chunking, embedding) is handled asynchronously by a dedicated worker service via SQS.

## 2. Functional Requirements

### 2.1 Authentication & User Management

- There is no self-registration. An admin user creates new users.
- When the admin creates a user, the system generates a random password and returns it once. This is the user's permanent password.
- Users log in with username and password.
- Sessions are managed via JWT access tokens (30-minute expiry) and refresh tokens (7-day expiry, httpOnly cookie).
- All document and QA endpoints require authentication.

### 2.2 Admin

- An initial admin user is seeded on first deployment via environment variables (`ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`).
- Admin users can create new users (generates a random 16-character password).
- Admin users can list all users and delete non-admin users.
- Admin endpoints require both authentication and the `admin` role.

### 2.3 Document Management

- **Upload**: Users select up to 5 TXT files (max 10 MB each) and click "Upload Documents". The backend uploads each file to S3, creates document metadata rows, creates a RAG job, and sends an SQS message. Processing happens asynchronously in the RAG worker.
- **List**: Users see a list of their uploaded documents with filename, type, status, and upload date.
- **View**: Users view document details including metadata and a text preview (first 500 characters).
- **Delete**: Users delete documents. The system soft-deletes in the database, removes associated embeddings from the vector store, and removes from S3.
- **Supported file types**: `.txt`.

### 2.4 Async RAG Pipeline

- Each upload creates a **RAG job** that groups all uploaded documents.
- Only one active RAG job (pending or processing) is allowed per user at a time, enforced by a unique partial index on `rag_jobs(user_id) WHERE status IN ('pending', 'processing')`.
- The RAG worker polls SQS, picks up the job, and processes each document independently (extract text, chunk, embed, store vectors).
- Per-document status: `processing` → `ready` | `failed`.
- Job status: `pending` → `processing` → `success` | `partial_success` | `failure`.
  - `success`: all documents processed successfully.
  - `partial_success`: some documents succeeded, some failed (`documents_failed > 0`).
  - `failure`: all documents failed.
- The frontend polls `GET /api/rag-jobs/active` while a job is in progress and shows per-document status.
- No cross-tab sync — a second browser tab only sees job status on page load or refresh.

### 2.5 Question Answering (RAG)

- Users submit a natural language question.
- The system embeds the question using Bedrock Titan Embeddings, then performs a cosine similarity search against stored chunks in PostgreSQL (pgvector).
- The system constructs a prompt with the top-K retrieved chunks as context and sends it to a Bedrock LLM (Claude Sonnet).
- The response includes the answer text and source document citations with relevance scores.

## 3. Non-Functional Requirements

- **File size limit**: 10 MB per upload.
- **Supported file types**: `.txt`.
- **Max files per upload**: 5.
- **Generated passwords**: System-generated, 16 characters, mixed alphanumeric + symbols.
- **Token security**: Access token in memory (not localStorage), refresh token in httpOnly secure cookie.
- **CORS**: Backend allows requests from the frontend origin only.

## 4. Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.14, FastAPI, SQLAlchemy, Pydantic |
| RAG Worker | Python 3.14, LangChain, SQS consumer (separate ECS service) |
| Frontend | SvelteKit (SPA mode), TypeScript, adapter-node |
| Database | PostgreSQL 18 (AWS RDS) |
| Object Storage | AWS S3 |
| Message Queue | AWS SQS |
| Vector Search | pgvector extension on PostgreSQL |
| LLM | Anthropic Claude Sonnet via Amazon Bedrock |
| Embeddings | Amazon Titan Embeddings V2 (via Bedrock) |
| Infrastructure | Terraform |
| Containers | Docker, AWS ECR |
| Deployment | AWS ECS Fargate, Application Load Balancer |
| CI/CD | GitHub Actions |

## 5. Design Decisions

### 5.1 PostgreSQL over DynamoDB

The data model is relational (users own documents, documents have metadata). PostgreSQL provides foreign keys, JOINs, transactional guarantees, and is the conventional choice for web applications. Query patterns are predictable and low-volume. RDS `db.t4g.micro` is cost-comparable to DynamoDB for this workload.

### 5.2 Text Extraction

Only `.txt` files are supported. Full text is decoded as UTF-8 for chunking and embedding; a truncated preview (first 500 characters) is stored in document metadata.

### 5.3 pgvector on RDS instead of Bedrock Knowledge Base

Using pgvector on the existing RDS PostgreSQL instance instead of Bedrock Knowledge Base + OpenSearch Serverless. This consolidates all data into a single database, avoids the cost of OpenSearch Serverless, and simplifies the infrastructure.

### 5.4 LangChain RAG Pipeline

The RAG pipeline (ingestion and query) uses LangChain instead of a custom implementation. This provides battle-tested components for text splitting, embeddings, vector storage, and retrieval, reducing the amount of custom code and ensuring well-tested integration between pipeline stages.

Key LangChain components:

- **Text splitting**: `RecursiveCharacterTextSplitter.from_tiktoken_encoder` — splits on natural text boundaries (paragraphs, sentences, words) with token-based length measurement via tiktoken `cl100k_base` encoding. 500 tokens per chunk, 50-token overlap.
- **Embeddings**: `BedrockEmbeddings` — wraps Bedrock Titan V2 for both ingestion and query-time embedding.
- **Vector storage**: `PGVector` — manages its own tables (`langchain_pg_collection`, `langchain_pg_embedding`) in PostgreSQL with JSONB metadata columns. Each embedding row stores chunk text, a 1024-dimension vector, and metadata (`document_id`, `user_id`, `filename`).
- **Retrieval**: `PGVector.as_retriever()` with metadata filtering — per-user document isolation via `user_id` filter in JSONB metadata.

Trade-offs vs. a custom pipeline:
- LangChain manages vector storage tables automatically — no custom `document_chunks` table or manual SQL for vector operations.
- Per-user isolation is achieved via JSONB metadata filtering rather than SQL foreign keys.
- Deleting a document requires explicit `vector_store.delete()` calls since there is no CASCADE from the `documents` table to LangChain's tables.

### 5.5 Bedrock Models

- **LLM**: `anthropic.claude-3-5-sonnet-20241022-v2:0` — strong reasoning, fast, cost-effective.
- **Embeddings**: `amazon.titan-embed-text-v2:0` — 1024-dimension vectors, called via Bedrock InvokeModel for each chunk and each query.

### 5.6 SvelteKit SPA Mode

SvelteKit runs in SPA mode with all data fetching via `fetch()` to the FastAPI backend. Frontend and backend are separate ECS services behind the same ALB, routed by path prefix (`/api/*` → backend, `/*` → frontend).

### 5.7 JWT Auth with bcrypt

- Passwords hashed with bcrypt (cost factor 12).
- Access token: 30-minute expiry, stored in frontend memory.
- Refresh token: 7-day expiry, httpOnly secure cookie, rotated on each use.
- JWT secret stored in AWS Secrets Manager, injected as ECS task environment variable.

### 5.8 Async RAG Pipeline via SQS

Document processing (text extraction, chunking, embedding) is decoupled from the upload request via SQS. This avoids ALB timeout issues (60s default) when processing large or multiple documents. A dedicated `kbqa-rag` ECS service polls SQS and processes documents independently. This also allows the worker to scale independently from the backend.

## 6. API Specification

Base path: `/api`

### 6.1 Health

**GET `/api/health`** — No auth

Response `200`:
```json
{ "status": "healthy", "timestamp": "2026-09-05T10:00:00Z" }
```

### 6.2 Auth

**POST `/api/auth/login`** — No auth

Request:
```json
{
  "username": "alice",
  "password": "secureP@ss1"
}
```

Response `200`:
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

Sets httpOnly cookie: `refresh_token=<jwt>; Path=/api/auth; Secure; SameSite=Strict; Max-Age=604800`

Errors: `401` (invalid credentials).

---

**POST `/api/auth/refresh`** — Cookie auth

Request: No body. Reads `refresh_token` from cookie.

Response `200`:
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

Rotates the refresh token cookie. Errors: `401` (expired/invalid refresh token).

---

**POST `/api/auth/logout`** — Bearer auth

Response `200`:
```json
{ "message": "Logged out" }
```

Clears the refresh token cookie.

### 6.3 Admin (User Management)

All admin endpoints require Bearer auth with `role: admin`.

**POST `/api/admin/users`** — Admin only

Request:
```json
{
  "username": "bob",
  "email": "bob@example.com"
}
```

Response `201`:
```json
{
  "id": "660e8400-...",
  "username": "bob",
  "email": "bob@example.com",
  "password": "aB3$kL9m!xR2pQ7w",
  "created_at": "2026-09-05T10:00:00Z"
}
```

The `password` is returned once and cannot be retrieved again. Errors: `409` (username/email exists), `403` (not admin).

---

**GET `/api/admin/users`** — Admin only

Response `200`:
```json
{
  "items": [
    {
      "id": "550e8400-...",
      "username": "alice",
      "email": "alice@example.com",
      "role": "user",
      "created_at": "2026-09-05T10:00:00Z"
    }
  ],
  "total": 5
}
```

---

**DELETE `/api/admin/users/{id}`** — Admin only

Response `200`:
```json
{ "message": "User deleted", "id": "660e8400-..." }
```

Cannot delete admin users. Errors: `404`, `403` (not admin or target is admin).

### 6.4 Documents

**POST `/api/documents/`** — Bearer auth

Request: `multipart/form-data` with field `files` (up to 5 TXT files).

Response `201`:
```json
{
  "job_id": "a1b2c3d4-...",
  "documents": [
    {
      "id": "d1a2b3c4-...",
      "filename": "notes.txt",
      "file_type": "txt",
      "file_size_bytes": 24576,
      "status": "processing"
    }
  ]
}
```

Errors: `400` (unsupported file type — only `.txt` allowed), `413` (file too large), `409` (a RAG job is already in progress).

---

**GET `/api/documents/`** — Bearer auth

Response `200`:
```json
{
  "items": [
    {
      "id": "d1a2b3c4-...",
      "filename": "notes.txt",
      "file_type": "txt",
      "file_size_bytes": 24576,
      "status": "ready",
      "created_at": "2026-09-05T10:05:00Z"
    }
  ],
  "total": 42
}
```

---

**GET `/api/documents/{id}`** — Bearer auth

Response `200`:
```json
{
  "id": "d1a2b3c4-...",
  "filename": "notes.txt",
  "file_type": "txt",
  "file_size_bytes": 24576,
  "s3_key": "documents/550e8400.../d1a2b3c4/notes.txt",
  "status": "ready",
  "text_preview": "This document covers the project requirements...",
  "created_at": "2026-09-05T10:05:00Z",
  "indexed_at": "2026-09-05T10:06:30Z"
}
```

Errors: `404` (not found or not owned by user).

---

**DELETE `/api/documents/{id}`** — Bearer auth

Response `200`:
```json
{ "message": "Document deleted", "id": "d1a2b3c4-..." }
```

Soft-deletes in DB, removes associated embeddings from the vector store, removes from S3. Errors: `404`.

### 6.5 RAG Jobs

**GET `/api/rag-jobs/active`** — Bearer auth

Returns the user's currently active RAG job (pending or processing), or `null`.

Response `200`:
```json
{
  "job": {
    "id": "a1b2c3d4-...",
    "status": "processing",
    "total_documents": 3,
    "documents_processed": 1,
    "documents_failed": 0,
    "created_at": "2026-09-05T10:05:00Z",
    "documents": [
      { "id": "d1a2b3c4-...", "filename": "notes.txt", "status": "ready" },
      { "id": "d2a3b4c5-...", "filename": "report.txt", "status": "processing" },
      { "id": "d3a4b5c6-...", "filename": "data.txt", "status": "processing" }
    ]
  }
}
```

Returns `{ "job": null }` when no active job exists.

---

**GET `/api/rag-jobs/`** — Bearer auth

Returns the user's RAG job history (all finished jobs).

Response `200`:
```json
{
  "items": [
    {
      "id": "a1b2c3d4-...",
      "status": "success",
      "total_documents": 3,
      "documents_processed": 3,
      "documents_failed": 0,
      "created_at": "2026-09-05T10:05:00Z",
      "completed_at": "2026-09-05T10:08:30Z"
    }
  ],
  "total": 12
}
```

### 6.6 Question Answering

**POST `/api/qa/ask`** — Bearer auth

Request:
```json
{
  "question": "What were Q3 2026 revenue figures?",
  "max_results": 5
}
```

Response `200`:
```json
{
  "answer": "According to the Q3 2026 report, total revenue was $4.2B...",
  "sources": [
    {
      "document_id": "d1a2b3c4-...",
      "filename": "report.txt",
      "excerpt": "Total revenue for Q3 2026 reached $4.2 billion...",
      "relevance_score": 0.92
    }
  ],
  "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0"
}
```

Errors: `422` (question must be 1-1000 characters).

## 7. Database Schema

### Table: `users`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | PK, default `gen_random_uuid()` |
| `username` | `VARCHAR(50)` | UNIQUE, NOT NULL |
| `email` | `VARCHAR(255)` | UNIQUE, NOT NULL |
| `password_hash` | `VARCHAR(255)` | NOT NULL |
| `role` | `VARCHAR(20)` | NOT NULL, default `'user'`, CHECK in ('admin','user') |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` |

Indexes: `ix_users_username` (unique), `ix_users_email` (unique).

The initial admin user is seeded during application startup if no admin exists, using `ADMIN_USERNAME`, `ADMIN_EMAIL`, and `ADMIN_PASSWORD` environment variables.

### Table: `rag_jobs`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | PK, default `gen_random_uuid()` |
| `user_id` | `UUID` | FK → `users.id`, NOT NULL |
| `status` | `VARCHAR(20)` | NOT NULL, default `'pending'` |
| `total_documents` | `INTEGER` | NOT NULL |
| `documents_processed` | `INTEGER` | NOT NULL, default `0` |
| `documents_failed` | `INTEGER` | NOT NULL, default `0` |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` |
| `completed_at` | `TIMESTAMPTZ` | NULLABLE |

Status values: `pending`, `processing`, `success`, `partial_success` (if `documents_failed > 0`), `failure`.

Indexes: unique partial index on `(user_id) WHERE status IN ('pending', 'processing')` to enforce one active job per user.

### Table: `rag_job_documents`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | PK, default `gen_random_uuid()` |
| `rag_job_id` | `UUID` | FK → `rag_jobs.id`, NOT NULL |
| `document_id` | `UUID` | FK → `documents.id`, NOT NULL |
| `status` | `VARCHAR(20)` | NOT NULL, default `'pending'` |
| `error_message` | `TEXT` | NULLABLE |
| `started_at` | `TIMESTAMPTZ` | NULLABLE |
| `completed_at` | `TIMESTAMPTZ` | NULLABLE |

Status values: `pending`, `processing`, `ready`, `failed`.

Indexes: unique index on `(rag_job_id, document_id)`.

### Table: `documents`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | PK, default `gen_random_uuid()` |
| `user_id` | `UUID` | FK → `users.id`, NOT NULL |
| `filename` | `VARCHAR(255)` | NOT NULL |
| `file_type` | `VARCHAR(10)` | NOT NULL, CHECK in ('txt') |
| `file_size_bytes` | `INTEGER` | NOT NULL |
| `s3_key` | `VARCHAR(512)` | NOT NULL, UNIQUE |
| `status` | `VARCHAR(20)` | NOT NULL, default `'pending'` |
| `text_preview` | `TEXT` | NULLABLE |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` |
| `indexed_at` | `TIMESTAMPTZ` | NULLABLE |
| `deleted_at` | `TIMESTAMPTZ` | NULLABLE (soft delete) |

Status values: `pending`, `ready`, `failed`.

Indexes: `ix_documents_user_id`, `ix_documents_status`, `ix_documents_s3_key` (unique).

### Vector Storage (LangChain PGVector)

Vector storage tables (`langchain_pg_collection`, `langchain_pg_embedding`) are created and managed automatically by LangChain's PGVector on first use. Each embedding row stores chunk text, a 1024-dimension vector, and JSONB metadata (`document_id`, `user_id`, `filename`) for per-user filtering.
