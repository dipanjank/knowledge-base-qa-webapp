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
               ┌──────────▼───┐   ┌──────────▼───┐   ┌────────▼────────┐
               │ RDS          │   │ S3 Bucket    │   │ Amazon Bedrock  │
               │ PostgreSQL   │   │ (documents)  │   │ - Titan Embed   │
               │ + pgvector   │   └──────────────┘   │ - LLM Invoke   │
               │ (users, docs,│                       └─────────────────┘
               │  chunks,     │
               │  vectors)    │
               └──────────────┘
```

## 2. Request Flows

### 2.1 Document Upload Flow

```
Browser                    ALB              Backend              S3         Bedrock Embed    RDS
  │                         │                  │                  │              │             │
  │── POST /api/documents ──▶                  │                  │              │             │
  │   (multipart file)      │── forward ──────▶│                  │              │             │
  │                         │                  │── validate type ─┤              │             │
  │                         │                  │   + size         │              │             │
  │                         │                  │                  │              │             │
  │                         │                  │── INSERT doc ────┼──────────────┼────────────▶│
  │                         │                  │   (status=       │              │             │
  │                         │                  │    processing)   │              │             │
  │                         │                  │                  │              │             │
  │                         │                  │── upload file ──▶│              │             │
  │                         │                  │                  │              │             │
  │                         │                  │── extract text ──┤              │             │
  │                         │                  │   (full text)    │              │             │
  │                         │                  │                  │              │             │
  │                         │                  │── chunk text ────┤              │             │
  │                         │                  │   (500 tokens,   │              │             │
  │                         │                  │    50 overlap)   │              │             │
  │                         │                  │                  │              │             │
  │                         │                  │── embed chunks ──┼─────────────▶│             │
  │                         │                  │   (Titan V2)     │              │             │
  │                         │                  │◀── vectors[] ────┼──────────────│             │
  │                         │                  │                  │              │             │
  │                         │                  │── INSERT chunks ─┼──────────────┼────────────▶│
  │                         │                  │   + vectors      │              │             │
  │                         │                  │                  │              │             │
  │                         │                  │── UPDATE doc ────┼──────────────┼────────────▶│
  │                         │                  │   (preview,      │              │             │
  │                         │                  │    status=       │              │             │
  │                         │                  │    indexed)      │              │             │
  │                         │                  │                  │              │             │
  │◀─── 201 document json ──│◀── response ─────│                  │              │             │
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
│       └── deploy.yml                  # Build, push ECR, deploy ECS
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
│   │   │   └── document_chunk.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── document.py
│   │   │   └── qa.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── admin.py
│   │   │   ├── documents.py
│   │   │   ├── qa.py
│   │   │   └── health.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── document_service.py
│   │   │   ├── s3_service.py
│   │   │   ├── embedding_service.py  # Bedrock Titan embedding calls
│   │   │   ├── chunking_service.py   # Text chunking logic
│   │   │   └── rag_service.py        # Vector search + LLM answer generation
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   └── auth_middleware.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── text_extraction.py
│   │       └── security.py             # JWT encode/decode, password hashing
│   └── tests/
│       ├── conftest.py
│       ├── test_auth.py
│       ├── test_documents.py
│       └── test_qa.py
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
│   │       │   ├── +page.svelte        # List + upload
│   │       │   └── [id]/
│   │       │       └── +page.svelte    # Document detail
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

## 4. AWS Infrastructure

### 4.1 Networking

- **VPC**: `10.0.0.0/16`
- **Public subnets**: `10.0.1.0/24` (AZ a), `10.0.2.0/24` (AZ b) — for ALB
- **Private subnets**: `10.0.10.0/24` (AZ a), `10.0.11.0/24` (AZ b) — for ECS, RDS
- **Internet Gateway**: Attached to VPC for public subnet routing
- **NAT Gateway**: In one public subnet for outbound traffic from private subnets

### 4.2 Security Groups

**ALB** (`sg-alb`):
- Ingress: 443/tcp from `0.0.0.0/0`, 80/tcp from `0.0.0.0/0` (redirect to 443)
- Egress: all to VPC CIDR

**ECS Tasks** (`sg-ecs`):
- Ingress: 3000/tcp and 8000/tcp from `sg-alb` only
- Egress: all (S3, Bedrock, Secrets Manager via NAT)

**RDS** (`sg-rds`):
- Ingress: 5432/tcp from `sg-ecs` only
- Egress: none

### 4.3 Application Load Balancer

- **Listener**: HTTPS :443
- **Default rule**: forward to frontend target group (port 3000)
- **Path rule**: `/api/*` → forward to backend target group (port 8000)
- **Health checks**: frontend `/`, backend `/api/health`

### 4.4 ECS (Fargate)

| Service | CPU | Memory | Port | Image |
|---------|-----|--------|------|-------|
| `kbqa-frontend` | 256 | 512 MiB | 3000 | `{ecr}/kbqa-frontend:{sha}` |
| `kbqa-backend` | 512 | 1024 MiB | 8000 | `{ecr}/kbqa-backend:{sha}` |

Backend environment variables (from Secrets Manager + task definition):
- `DATABASE_URL`, `JWT_SECRET`, `AWS_REGION`, `S3_BUCKET_NAME`, `BEDROCK_MODEL_ID`, `BEDROCK_EMBEDDING_MODEL_ID`, `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`

### 4.5 RDS PostgreSQL

- Engine: PostgreSQL 18
- Instance: `db.t4g.micro`
- Storage: 20 GB gp3
- Multi-AZ: No (v1)
- Database name: `kbqa`
- Credentials: AWS Secrets Manager
- Extensions: `pgvector` (for vector similarity search), `uuid-ossp`

### 4.6 S3

- Bucket: `kbqa-documents-{account_id}`
- Server-side encryption: AES-256
- Key pattern: `documents/{user_id}/{document_id}.{ext}`

### 4.7 IAM

- **ECS Task Execution Role**: Pull ECR images, write CloudWatch logs, read Secrets Manager
- **ECS Task Role**: S3 read/write on documents bucket, Bedrock InvokeModel (for Titan Embeddings and Claude Sonnet)

### 4.8 Terraform Resource Summary

| Module | Key Resources |
|--------|---------------|
| `networking` | VPC, subnets (2 public, 2 private), IGW, NAT GW, route tables |
| `alb` | ALB, 2 target groups, HTTPS listener, path-based rules, SG |
| `ecs` | Cluster, 2 task definitions, 2 services, SG, CloudWatch log groups |
| `ecr` | 2 repositories (frontend, backend) |
| `rds` | PostgreSQL instance, subnet group, SG |
| `s3` | Documents bucket, encryption config, bucket policy |
| `iam` | Execution role, task role, policy attachments |

## 5. CI/CD Pipeline

### 5.1 CI Workflow (`ci.yml`) — Runs on PR to `main`

Three parallel jobs:
1. **backend-lint-test**: Python 3.14, `ruff check`, `pytest`
2. **frontend-lint-test**: Node 22, `npm run lint`, `npm run check`, `npm test`
3. **terraform-validate**: `terraform init -backend=false`, `terraform validate`

### 5.2 Deploy Workflow (`deploy.yml`) — Runs on push to `main`

1. Checkout code
2. Configure AWS credentials (OIDC role assumption)
3. Login to ECR
4. Build and push backend image tagged with commit SHA
5. Build and push frontend image tagged with commit SHA
6. Force new deployment on both ECS services

## 6. Document Processing Pipeline

### Text Extraction

| File Type | Library | Strategy |
|-----------|---------|----------|
| PDF | pdfplumber | Extract full text from all pages. First 500 chars used as preview. Count total pages. |
| TXT | stdlib | Read full text. First 500 chars used as preview. |
| CSV | stdlib csv | Read all rows, join as comma-separated text. First 500 chars used as preview. |

### Chunking

- Fixed-size chunking: 500 tokens per chunk, 50-token overlap.
- Each chunk is stored with its parent `document_id` and `chunk_index`.

### Embedding

- Each chunk is embedded via Bedrock `InvokeModel` using `amazon.titan-embed-text-v2:0`.
- Produces a 1024-dimension vector per chunk.
- Chunks and vectors are batch-inserted into the `document_chunks` table.

### S3 Key Convention

`documents/{user_id}/{document_id}.{extension}`

### Upload Flow Summary

1. Validate file type and size
2. INSERT document metadata (status=`processing`)
3. Upload file to S3
4. Extract full text from file
5. Chunk text (500 tokens, 50 overlap)
6. Embed each chunk via Bedrock Titan
7. INSERT chunks + vectors into `document_chunks`
8. UPDATE document (preview, status=`indexed`)

### Delete Flow

1. Set `deleted_at = now()`, `status = 'deleted'` in RDS
2. DELETE all rows from `document_chunks` where `document_id` matches
3. Delete object from S3

## 7. RAG Prompt Template

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

## 8. Frontend Routes

| Route | Auth | Description |
|-------|------|-------------|
| `/` | No | Redirect to `/qa` if logged in, else `/login` |
| `/login` | No | Username/password form |
| `/admin/users` | Yes (admin) | Create users, list users, delete users |
| `/documents` | Yes | Upload files, view paginated document list, delete documents |
| `/documents/[id]` | Yes | Document detail with metadata and text preview |
| `/qa` | Yes | Chat interface: ask questions, view answers with source citations |
