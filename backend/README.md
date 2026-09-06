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
- **`dependencies.py`** — FastAPI `Depends` wiring: `get_user_repo` → `get_auth_service` / `get_admin_service`, plus `get_current_user` and `require_admin` guards.

### Models

| File | Description |
|------|-------------|
| `models/user.py` | `User` table — UUID PK, username, email, password_hash, role (admin/user), timestamps |

### Repositories

| File | Description |
|------|-------------|
| `repositories/base.py` | `GenericRepository[T]` — reusable async CRUD: `get_by_id`, `get_one(**filters)`, `get_all`, `count`, `create`, `delete` |
| `repositories/user_repository.py` | Extends `GenericRepository[User]`, adds `get_by_username_or_email` (OR query) |

### Services

| File | Description |
|------|-------------|
| `services/auth_service.py` | `login()` — validates credentials, returns access + refresh tokens. `refresh()` — rotates tokens. |
| `services/admin_service.py` | `create_user()` — generates random password, checks uniqueness. `list_users()`, `delete_user()` — with admin/not-found guards. |

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

### Schemas

| File | Classes |
|------|---------|
| `schemas/auth.py` | `LoginRequest`, `TokenResponse` |
| `schemas/user.py` | `CreateUserRequest`, `CreateUserResponse`, `UserResponse`, `UserListResponse`, `MessageResponse` |

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
| `BEDROCK_MODEL_ID` | Bedrock LLM model ID |
| `BEDROCK_EMBEDDING_MODEL_ID` | Bedrock embedding model ID |
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
BEDROCK_MODEL_ID=test \
BEDROCK_EMBEDDING_MODEL_ID=test \
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

## Linting

```bash
ruff check app/ tests/
```

## Database

Tables are created manually via `sql/kbqa.sql` applied to RDS — no auto-migration. The admin user is seeded on startup if no admin exists.
