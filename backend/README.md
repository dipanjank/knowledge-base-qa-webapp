# Backend — Knowledge Base QA API

FastAPI REST API for authentication, user management, document processing, and RAG-based question answering.

## Tech Stack

- Python 3.14, FastAPI, SQLModel, Pydantic
- PostgreSQL 18 with pgvector (via asyncpg)
- JWT authentication (access + refresh tokens)
- Amazon Bedrock (Claude Sonnet for LLM, Titan V2 for embeddings)
- bcrypt for password hashing

## Architecture

```
routers/          HTTP layer (request/response, cookies, status codes)
  └──► services/      Business logic (validation, orchestration)
         └──► repositories/  Data access (async DB queries)
                └──► models/       SQLModel ORM definitions
```

- **`main.py`** — App entrypoint. Registers routers, seeds admin user on startup via lifespan hook.
- **`config.py`** — All settings loaded from environment variables (no defaults). Uses `pydantic-settings`.
- **`database.py`** — Async SQLAlchemy engine and session factory (`asyncpg` driver).
- **`dependencies.py`** — FastAPI `Depends` wiring: `get_user_repo` → `get_auth_service` / `get_admin_service`, `get_document_repo` / `get_rag_job_repo` → `get_document_service` / `get_rag_job_service`, `get_s3_service`, `get_sqs_service`, plus `get_current_user` and `require_admin` guards.

### Models

| File | Description |
|------|-------------|
| `models/user.py` | `User` table — UUID PK, username, email, password_hash, role (admin/user), timestamps |
| `models/document.py` | `Document` table — UUID PK, user_id, filename, file_type, file_size_bytes, s3_key (unique), status, text_preview, timestamps, soft delete |
| `models/rag_job.py` | `RagJob` table — UUID PK, user_id, status, total_documents, documents_processed, documents_failed, timestamps. `RagJobDocument` junction table linking jobs to documents with per-document status and error_message |

### Repositories

| File | Description |
|------|-------------|
| `repositories/base.py` | `GenericRepository[T]` — reusable async CRUD: `get_by_id`, `get_one(**filters)`, `get_all`, `count`, `create`, `delete` |
| `repositories/user_repository.py` | Extends `GenericRepository[User]`, adds `get_by_username_or_email` (OR query) |
| `repositories/document_repository.py` | Extends `GenericRepository[Document]` — `get_by_user`, `count_by_user`, `get_by_id_and_user`, `soft_delete` (sets deleted_at + cleans up embeddings from langchain_pg_embedding) |
| `repositories/rag_job_repository.py` | Extends `GenericRepository[RagJob]` — `get_active_job`, `get_user_jobs`, `count_user_jobs`, `get_job_documents`, `create_job_document` |

### Services

| File | Description |
|------|-------------|
| `services/auth_service.py` | `login()` — validates credentials, returns access + refresh tokens. `refresh()` — rotates tokens. |
| `services/admin_service.py` | `create_user()` — generates random password, checks uniqueness. `list_users()`, `delete_user()` — with admin/not-found guards. |
| `services/document_service.py` | `upload_documents()` — validates files (max 5, .txt only), uploads to S3, creates Document + RagJob rows, sends SQS message. `list_documents()`, `delete_document()` (soft delete). |
| `services/rag_job_service.py` | `get_active_job()` — returns current pending/processing job with per-document statuses. `list_jobs()` — paginated job history. |
| `services/s3_service.py` | boto3 S3 wrapper — `upload_file(key, data, content_type)` via `put_object` |
| `services/sqs_service.py` | boto3 SQS wrapper — `send_message(body)` with JSON serialization |

### Routers

| Route | Method | Auth | Description |
|-------|--------|------|-------------|
| `/api/health` | GET | None | Health check |
| `/api/auth/login` | POST | None | Login, returns access token + sets refresh cookie |
| `/api/auth/refresh` | POST | Cookie | Rotate tokens |
| `/api/auth/logout` | POST | Bearer | Clear refresh cookie |
| `/api/admin/users` | POST | Admin | Create user, returns generated password |
| `/api/admin/users` | GET | Admin | List all users |
| `/api/admin/users/{id}` | DELETE | Admin | Delete non-admin user |
| `/api/documents/` | POST | Bearer | Upload up to 5 files, creates RAG job, sends SQS message (201) |
| `/api/documents/` | GET | Bearer | List user's documents (excludes soft-deleted) |
| `/api/documents/{id}` | DELETE | Bearer | Soft-delete document + clean up embeddings |
| `/api/rag-jobs/active` | GET | Bearer | Current pending/processing job with per-document statuses |
| `/api/rag-jobs/` | GET | Bearer | Job history, most recent first |

### Schemas

| File | Classes |
|------|---------|
| `schemas/auth.py` | `LoginRequest`, `TokenResponse` |
| `schemas/user.py` | `CreateUserRequest`, `CreateUserResponse`, `UserResponse`, `UserListResponse`, `MessageResponse` |
| `schemas/document.py` | `DocumentInfo`, `DocumentUploadResponse`, `DocumentResponse`, `DocumentListResponse` |
| `schemas/rag_job.py` | `RagJobDocumentStatus`, `RagJobResponse`, `RagJobListResponse` |

### Utils

| File | Description |
|------|-------------|
| `utils/auth.py` | `hash_password`, `verify_password`, `generate_password` (16-char), `create_access_token`, `create_refresh_token`, `decode_token` |

## Environment Variables

All are required — no defaults.

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `JWT_SECRET` | Secret key for signing JWTs |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL in minutes |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL in days |
| `AWS_REGION` | AWS region |
| `S3_BUCKET_NAME` | S3 bucket for document storage |
| `SQS_QUEUE_URL` | SQS queue URL for RAG job processing |
| `ADMIN_USERNAME` | Seed admin username |
| `ADMIN_EMAIL` | Seed admin email |
| `ADMIN_PASSWORD` | Seed admin password |

## Development

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload          # Dev server on :8000
```

## Testing

```bash
# All env vars must be supplied (no defaults)
DATABASE_URL=postgresql://x:x@localhost/x \
JWT_SECRET=test-secret \
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30 \
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7 \
AWS_REGION=us-east-1 \
S3_BUCKET_NAME=test \
SQS_QUEUE_URL=http://localhost:4566/queue/test \
ADMIN_USERNAME=admin \
ADMIN_EMAIL=admin@test.com \
ADMIN_PASSWORD=admin \
pytest -v
```

Tests use async SQLite in-memory for repository tests and mocked repositories for service tests.

| File | Tests | Strategy |
|------|-------|----------|
| `test_user_repository.py` | 11 | Real async SQLite DB |
| `test_auth_service.py` | 7 | Mocked `UserRepository` |
| `test_admin_service.py` | 7 | Mocked `UserRepository` |
| `test_health.py` | 1 | `TestClient` |
| `test_document_repository.py` | 9 | Real async SQLite DB |
| `test_rag_job_repository.py` | 8 | Real async SQLite DB |
| `test_document_service.py` | 8 | Mocked repos + services |
| `test_rag_job_service.py` | 5 | Mocked `RagJobRepository` |
| `test_s3_service.py` | 3 | Mocked boto3 client |
| `test_sqs_service.py` | 2 | Mocked boto3 client |

## Linting

```bash
ruff check app/ tests/
```

## Database

Tables are created manually via `sql/kbqa.sql` applied to RDS — no auto-migration. The admin user is seeded on startup if no admin exists.
