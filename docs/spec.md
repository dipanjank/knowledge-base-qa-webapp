# Knowledge Base QA Web Application — System Specification

## 1. Overview

A fullstack web application that allows users to upload documents (PDF, TXT, CSV), chunk and embed them using Amazon Bedrock Titan Embeddings, store vectors in PostgreSQL with pgvector, and perform RAG-based question answering against the indexed content.

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

- **Upload**: Users upload PDF, TXT, or CSV files (max 10 MB). The system saves the file to S3, extracts full text, chunks the text, generates embeddings via Bedrock Titan, stores chunks with vectors in PostgreSQL (pgvector), and saves metadata.
- **List**: Users see a paginated list of their uploaded documents with filename, type, status, and upload date.
- **View**: Users view document details including metadata and a text preview (first 500 characters).
- **Delete**: Users delete documents. The system soft-deletes in the database, deletes associated chunks, and removes from S3.

### 2.4 Question Answering (RAG)

- Users submit a natural language question.
- The system embeds the question using Bedrock Titan Embeddings, then performs a cosine similarity search against stored chunks in PostgreSQL (pgvector).
- The system constructs a prompt with the top-K retrieved chunks as context and sends it to a Bedrock LLM (Claude Sonnet).
- The response includes the answer text and source document citations with relevance scores.

## 3. Non-Functional Requirements

- **File size limit**: 10 MB per upload.
- **Supported file types**: `.pdf`, `.txt`, `.csv`.
- **Generated passwords**: System-generated, 16 characters, mixed alphanumeric + symbols.
- **Token security**: Access token in memory (not localStorage), refresh token in httpOnly secure cookie.
- **CORS**: Backend allows requests from the frontend origin only.

## 4. Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.14, FastAPI, SQLAlchemy, Pydantic |
| Frontend | SvelteKit (SPA mode), TypeScript, adapter-node |
| Database | PostgreSQL 18 (AWS RDS) |
| Object Storage | AWS S3 |
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

### 5.2 pdfplumber for PDF Text Extraction

pdfplumber produces higher-quality text extraction than PyPDF2, especially for PDFs with complex layouts and tables. For CSV, the stdlib `csv` module is sufficient. Full text is extracted for chunking and embedding; a truncated preview is stored in document metadata.

### 5.3 pgvector on RDS instead of Bedrock Knowledge Base

Using pgvector on the existing RDS PostgreSQL instance instead of Bedrock Knowledge Base + OpenSearch Serverless. This consolidates all data into a single database, gives full control over the chunking and embedding pipeline, avoids the cost of OpenSearch Serverless, and simplifies the infrastructure. The trade-off is that chunking and embedding logic must be implemented in the application.

### 5.4 Chunking Strategy

- Fixed-size chunking: 500 tokens per chunk with 50-token overlap.
- Chunks are stored in a `document_chunks` table with their embedding vectors.
- Each chunk retains a reference to its parent document and its position (chunk index).

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

**POST `/api/documents/upload`** — Bearer auth

Request: `multipart/form-data` with field `file`.

Response `201`:
```json
{
  "id": "d1a2b3c4-...",
  "filename": "report.pdf",
  "file_type": "pdf",
  "file_size_bytes": 245760,
  "s3_key": "documents/550e8400.../d1a2b3c4.pdf",
  "status": "processing",
  "text_preview": null,
  "created_at": "2026-09-05T10:05:00Z"
}
```

Errors: `415` (unsupported file type), `413` (file too large).

---

**GET `/api/documents?page=1&page_size=20`** — Bearer auth

Response `200`:
```json
{
  "items": [
    {
      "id": "d1a2b3c4-...",
      "filename": "report.pdf",
      "file_type": "pdf",
      "file_size_bytes": 245760,
      "status": "indexed",
      "created_at": "2026-09-05T10:05:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

---

**GET `/api/documents/{id}`** — Bearer auth

Response `200`:
```json
{
  "id": "d1a2b3c4-...",
  "filename": "report.pdf",
  "file_type": "pdf",
  "file_size_bytes": 245760,
  "s3_key": "documents/550e8400.../d1a2b3c4.pdf",
  "status": "indexed",
  "text_preview": "This report covers Q3 2026 financial results...",
  "page_count": 12,
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

Soft-deletes in DB, deletes associated chunks, removes from S3. Errors: `404`.

### 6.5 Question Answering

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
      "filename": "report.pdf",
      "excerpt": "Total revenue for Q3 2026 reached $4.2 billion...",
      "relevance_score": 0.92
    }
  ],
  "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0"
}
```

Errors: `422` (question must be 1–1000 characters).

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

### Table: `documents`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | PK, default `gen_random_uuid()` |
| `user_id` | `UUID` | FK → `users.id`, NOT NULL |
| `filename` | `VARCHAR(255)` | NOT NULL |
| `file_type` | `VARCHAR(10)` | NOT NULL, CHECK in ('pdf','txt','csv') |
| `file_size_bytes` | `INTEGER` | NOT NULL |
| `s3_key` | `VARCHAR(512)` | NOT NULL, UNIQUE |
| `status` | `VARCHAR(20)` | NOT NULL, default 'processing' |
| `text_preview` | `TEXT` | NULLABLE |
| `page_count` | `INTEGER` | NULLABLE |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` |
| `indexed_at` | `TIMESTAMPTZ` | NULLABLE |
| `deleted_at` | `TIMESTAMPTZ` | NULLABLE (soft delete) |

Status values: `processing`, `indexed`, `failed`, `deleted`.

Indexes: `ix_documents_user_id`, `ix_documents_status`, `ix_documents_s3_key` (unique).

### Table: `document_chunks`

Requires pgvector extension: `CREATE EXTENSION IF NOT EXISTS vector;`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | PK, default `gen_random_uuid()` |
| `document_id` | `UUID` | FK → `documents.id`, NOT NULL |
| `chunk_index` | `INTEGER` | NOT NULL |
| `chunk_text` | `TEXT` | NOT NULL |
| `embedding` | `VECTOR(1024)` | NOT NULL |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` |

Indexes: `ix_document_chunks_document_id`, HNSW index on `embedding` column using cosine distance for fast similarity search.

Cascade delete: when a document is deleted, all its chunks are deleted.
