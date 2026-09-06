# System Design and Architecture

## 1. High-Level Architecture

```
                         ┌───────────────────┐
                         │   Public ALB       │
                         │   (HTTPS :443)     │
                         └────┬──────────┬────┘
                              │          │
                     /* routes    /api/* routes
                              │          │
               ┌──────────────▼──┐  ┌────▼──────────────┐
               │ ECS Fargate     │  │ ECS Fargate        │
               │ Frontend        │  │ Backend            │
               │ (SvelteKit)     │  │ (FastAPI)          │
               │ :3000           │  │ :8000              │
               └─────────────────┘  └──┬─────┬──────┬───┘
                                       │     │      │
                          ┌────────────┘     │      └──────────┐
                          │                  │                  │
               ┌──────────▼───┐   ┌──────────▼───┐        ┌────▼────┐
               │ RDS          │   │ S3 Bucket    │        │  SQS    │
               │ PostgreSQL   │   │ (documents)  │        │  Queue  │
               │ + pgvector   │   └──────┬───────┘        └────┬────┘
               │ (users, docs,│          │                     │
               │  chunks,     │          │                     │
               │  vectors,    │   ┌──────▼─────────────────────▼────┐
               │  rag_jobs)   │   │ ECS Fargate                     │
               └──────┬───────┘   │ RAG Worker (kbqa-rag)           │
                      │           │ - Polls SQS                     │
                      │           │ - Downloads from S3              │
                      │           │ - Embeds via Bedrock Titan       │
                      │           │ - Writes chunks + vectors to DB  │
                      │           └─────────────────────┬───────────┘
                      │                                 │
                      └─────────────────────────────────┘
                                                ┌─────────────────┐
                                                │ Amazon Bedrock  │
                                                │ - Titan Embed   │
                                                │ - LLM Invoke    │
                                                └─────────────────┘
```

## 2. Request Flows

### 2.1 Document Upload Flow (Async)

Upload is split into two phases: the synchronous upload (Backend) and async processing (RAG Worker).

**Phase 1: Upload (Backend — synchronous)**

```
Browser                    ALB              Backend              S3           SQS            RDS
  │                         │                  │                  │             │              │
  │── POST /api/documents ──▶                  │                  │             │              │
  │   (multipart, ≤5 files) │── forward ──────▶│                  │             │              │
  │                         │                  │── validate type ─┤             │              │
  │                         │                  │   + size         │             │              │
  │                         │                  │                  │             │              │
  │                         │                  │── INSERT rag_job ┼─────────────┼─────────────▶│
  │                         │                  │   (status=pending)             │              │
  │                         │                  │                  │             │              │
  │                         │                  │  FOR EACH FILE:  │             │              │
  │                         │                  │── upload file ──▶│             │              │
  │                         │                  │── INSERT doc ────┼─────────────┼─────────────▶│
  │                         │                  │   (status=       │             │              │
  │                         │                  │    processing,   │             │              │
  │                         │                  │    rag_job_id)   │             │              │
  │                         │                  │                  │             │              │
  │                         │                  │── SendMessage ───┼────────────▶│              │
  │                         │                  │   {job_id}       │             │              │
  │                         │                  │                  │             │              │
  │◀── 201 {job_id, docs} ──│◀── response ─────│                  │             │              │
```

**Phase 2: Processing (RAG Worker — async)**

```
SQS            RAG Worker                    S3         Bedrock Embed    RDS
  │                │                          │              │             │
  │── Receive ────▶│                          │              │             │
  │   {job_id}     │                          │              │             │
  │                │── UPDATE rag_job ─────────┼──────────────┼────────────▶│
  │                │   (status=processing)    │              │             │
  │                │                          │              │             │
  │                │  FOR EACH DOCUMENT:      │              │             │
  │                │── GET object ───────────▶│              │             │
  │                │◀── file bytes ───────────│              │             │
  │                │── extract text ───────────┤              │             │
  │                │── chunk text ─────────────┤              │             │
  │                │── embed chunks ───────────┼─────────────▶│             │
  │                │◀── vectors[] ─────────────┼──────────────│             │
  │                │── INSERT chunks + vectors ┼──────────────┼────────────▶│
  │                │── UPDATE doc (ready) ─────┼──────────────┼────────────▶│
  │                │── UPDATE rag_job ─────────┼──────────────┼────────────▶│
  │                │   (documents_processed++) │              │             │
  │                │                          │              │             │
  │                │── UPDATE rag_job ─────────┼──────────────┼────────────▶│
  │                │   (status=success/         │              │             │
  │                │    partial_success/failure)│              │             │
  │◀── Delete ────│                          │              │             │
```

### 2.2 RAG Query Flow

```
Browser                    ALB              Backend          Bedrock Embed   Bedrock LLM     RDS (pgvector)
  │                         │                  │                  │               │             │
  │── POST /api/qa/ask ────▶│                  │                  │               │             │
  │   { question }          │── forward ──────▶│                  │               │             │
  │                         │                  │                  │               │             │
  │                         │                  │── embed question▶│               │             │
  │                         │                  │   (Titan V2)     │               │             │
  │                         │                  │◀── query vector ─│               │             │
  │                         │                  │                  │               │             │
  │                         │                  │── cosine search ─┼───────────────┼────────────▶│
  │                         │                  │   (top K chunks) │               │             │
  │                         │                  │◀── chunks[] + ───┼───────────────┼─────────────│
  │                         │                  │   doc metadata   │               │             │
  │                         │                  │                  │               │             │
  │                         │                  │── build prompt ──┤               │             │
  │                         │                  │   (context +     │               │             │
  │                         │                  │    question)     │               │             │
  │                         │                  │                  │               │             │
  │                         │                  │── InvokeModel() ─┼──────────────▶│             │
  │                         │                  │   (Claude)       │               │             │
  │                         │                  │◀── answer ───────┼───────────────│             │
  │                         │                  │                  │               │             │
  │◀─── 200 { answer, ─────│◀── response ─────│                  │               │             │
  │     sources[] }         │                  │                  │               │             │
```

### 2.3 Auth Flow

```
Browser                    ALB              Backend                              RDS
  │                         │                  │                                  │
  │── POST /api/auth/login ▶│── forward ──────▶│                                  │
  │   { username, password } │                 │── SELECT user by username ──────▶│
  │                         │                  │◀── user record ──────────────────│
  │                         │                  │                                  │
  │                         │                  │── bcrypt.verify(password, hash) ─┤
  │                         │                  │                                  │
  │                         │                  │── create JWT access token ───────┤
  │                         │                  │── create JWT refresh token ──────┤
  │                         │                  │                                  │
  │◀─ 200 { access_token } ─│◀── response ─────│                                  │
  │   Set-Cookie: refresh   │                  │                                  │
  │                         │                  │                                  │
  │── GET /api/documents ──▶│── forward ──────▶│                                  │
  │   Authorization: Bearer │                  │── decode JWT, extract user_id ──┤
  │                         │                  │── query documents ──────────────▶│
  │◀─── 200 documents[] ───│◀── response ─────│                                  │
  │                         │                  │                                  │
  │   (token expires)       │                  │                                  │
  │── POST /api/auth/refresh▶│── forward ──────▶│                                  │
  │   Cookie: refresh_token │                  │── validate refresh token ────────┤
  │                         │                  │── issue new access + refresh ────┤
  │◀─ 200 { access_token } ─│◀── response ─────│                                  │
  │   Set-Cookie: refresh   │                  │                                  │
```

### 2.4 Admin User Creation Flow

```
Admin Browser              ALB              Backend                              RDS
  │                         │                  │                                  │
  │── POST /api/admin/users▶│── forward ──────▶│                                  │
  │   { username, email }   │                  │── check caller role == admin ────┤
  │                         │                  │── generate random 16-char pass ──┤
  │                         │                  │── bcrypt.hash(password) ──────────┤
  │                         │                  │── INSERT user ──────────────────▶│
  │                         │                  │                                  │
  │◀─ 201 { user,          ─│◀── response ─────│                                  │
  │   password }            │                  │                                  │
```

## 3. Monorepo Directory Layout

```
knowledge-base-qa-webapp/
├── .github/
│   └── workflows/
│       ├── ci.yml                      # Lint + test on PR
│       ├── deploy.yml                  # Build, push ECR, deploy ECS
│       └── rag-service.yml             # RAG worker lint, test, build, push ECR
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI app, router wiring, CORS
│   │   ├── config.py                   # Pydantic Settings (env vars)
│   │   ├── database.py                 # SQLAlchemy engine + session
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── document.py
│   │   │   └── rag_job.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── document.py
│   │   │   ├── rag_job.py
│   │   │   └── qa.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── admin.py
│   │   │   ├── documents.py
│   │   │   ├── rag_jobs.py
│   │   │   ├── qa.py
│   │   │   └── health.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── document_service.py
│   │   │   ├── s3_service.py
│   │   │   ├── sqs_service.py          # SQS SendMessage
│   │   │   ├── rag_job_service.py
│   │   │   └── rag_service.py          # Vector search + LLM answer generation
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── user_repository.py
│   │   │   ├── document_repository.py
│   │   │   ├── document_chunk_repository.py
│   │   │   └── rag_job_repository.py
│   │   ├── dependencies.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── security.py             # JWT encode/decode, password hashing
│   └── tests/
│       ├── conftest.py
│       ├── test_auth.py
│       ├── test_documents.py
│       └── test_qa.py
├── rag-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── VERSION
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py                   # Worker-specific Settings
│   │   ├── database.py                 # Async SQLAlchemy engine + session
│   │   ├── worker.py                   # SQS consumer loop
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── document.py             # Document + DocumentChunk (shared schema)
│   │   │   └── rag_job.py              # RagJob (shared schema)
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── s3_service.py           # S3 download
│   │       ├── embedding_service.py    # Bedrock Titan V2 embeddings
│   │       └── text_processing_service.py  # Text extraction + chunking
│   └── tests/
│       └── conftest.py
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── svelte.config.js
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── src/
│   │   ├── app.html
│   │   ├── app.css
│   │   ├── lib/
│   │   │   ├── api.ts                  # Fetch wrapper with auth + refresh
│   │   │   ├── stores/
│   │   │   │   ├── auth.ts
│   │   │   │   └── documents.ts
│   │   │   └── components/
│   │   │       ├── Navbar.svelte
│   │   │       ├── FileUpload.svelte
│   │   │       ├── DocumentList.svelte
│   │   │       ├── DocumentCard.svelte
│   │   │       ├── ChatWindow.svelte
│   │   │       ├── MessageBubble.svelte
│   │   │       ├── UserManagement.svelte
│   │   │       └── ProtectedRoute.svelte
│   │   └── routes/
│   │       ├── +layout.svelte
│   │       ├── +page.svelte            # Landing / redirect
│   │       ├── login/
│   │       │   └── +page.svelte
│   │       ├── admin/
│   │       │   └── users/
│   │       │       └── +page.svelte    # Admin user management
│   │       ├── documents/
│   │       │   ├── +page.svelte        # List + upload + active job status
│   │       │   └── [id]/
│   │       │       └── +page.svelte    # Document detail
│   │       ├── rag-jobs/
│   │       │   └── +page.svelte        # RAG job history
│   │       └── qa/
│   │           └── +page.svelte        # Chat interface
│   └── static/
│       └── favicon.png
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── providers.tf
│   ├── versions.tf
│   └── modules/
│       ├── networking/
│       ├── ecs/
│       ├── rds/
│       ├── s3/
│       ├── ecr/
│       ├── alb/
│       └── iam/
├── docs/
│   ├── spec.md
│   ├── architecture.md
│   └── tasks.md
├── docker-compose.yml
├── CLAUDE.md
├── README.md
└── .gitignore
```

## 4. CI/CD Pipeline

### 4.1 CI Workflow (`ci.yml`) — Runs on PR to `main`

Three parallel jobs:
1. **backend-lint-test**: Python 3.14, `ruff check`, `pytest`
2. **frontend-lint-test**: Node 22, `npm run lint`, `npm run check`, `npm test`
3. **terraform-validate**: `terraform init -backend=false`, `terraform validate`

### 4.2 Deploy Workflow (`deploy.yml`) — Runs on push to `main`

1. Checkout code
2. Configure AWS credentials (OIDC role assumption)
3. Login to ECR
4. Build and push backend image tagged with commit SHA
5. Build and push frontend image tagged with commit SHA
6. Force new deployment on both ECS services

### 4.3 RAG Service Workflow (`rag-service.yml`) — Runs on push to `main` (rag-service/ changes)

1. Checkout code
2. Configure AWS credentials (OIDC role assumption)
3. Login to ECR
4. Build and push rag-service image tagged with commit SHA
5. Force new deployment on kbqa-rag ECS service

## 5. Document Processing Pipeline

### Text Extraction

| File Type | Library | Strategy |
|-----------|---------|----------|
| TXT | stdlib | Decode as UTF-8. First 500 chars used as preview. |

### Chunking

- Fixed-size chunking: 500 tokens per chunk, 50-token overlap.
- Each chunk is stored with its parent `document_id` and `chunk_index`.

### Embedding

- Each chunk is embedded via Bedrock `InvokeModel` using `amazon.titan-embed-text-v2:0`.
- Produces a 1024-dimension vector per chunk.
- Chunks and vectors are batch-inserted into the `document_chunks` table.

### S3 Key Convention

`documents/{user_id}/{document_id}/{filename}`

### Upload Flow Summary (Async)

**Phase 1 (Backend — synchronous):**
1. Validate file types (.txt only) and sizes (max 10 MB)
2. INSERT rag_job (status=`pending`)
3. For each file: upload to S3, INSERT document (status=`processing`, rag_job_id)
4. Send SQS message with job_id
5. Return 201 with job_id and document list

**Phase 2 (RAG Worker — async):**
1. Receive SQS message with job_id
2. UPDATE rag_job (status=`processing`)
3. For each document:
   - Download file from S3
   - Extract text (UTF-8 decode)
   - Chunk text (500 tokens, 50 overlap)
   - Embed each chunk via Bedrock Titan
   - INSERT chunks + vectors into document_chunks
   - UPDATE document (preview, status=`ready`) or (status=`failed`)
   - UPDATE rag_job (documents_processed++ or documents_failed++)
4. UPDATE rag_job final status (success/partial_success/failure)
5. Delete SQS message

### Delete Flow

1. Set `deleted_at = now()` in RDS
2. DELETE all rows from `document_chunks` where `document_id` matches
3. Delete object from S3

## 6. RAG Prompt Template

```
You are a helpful assistant that answers questions based on the provided context documents.
Use ONLY the information from the context below to answer the question. If the context does
not contain enough information, say so clearly.

Context:
---
{chunk_1_text}
[Source: {filename_1}]
---
{chunk_2_text}
[Source: {filename_2}]
---

Question: {user_question}

Provide a clear, concise answer with references to the source documents.
```
