# Knowledge Base QA

A fullstack web application for uploading documents (PDF, TXT, CSV), chunking and embedding them with pgvector, and performing RAG-based question answering via Amazon Bedrock.

## How It Works

1. Admin creates user accounts (no self-registration)
2. Users upload documents, which are stored in S3, chunked (500 tokens, 50 overlap), and embedded using Amazon Titan V2
3. Embeddings are stored in PostgreSQL with pgvector for cosine similarity search
4. Users ask natural language questions — the system retrieves relevant chunks, constructs a prompt, and gets an answer from Claude Sonnet via Bedrock
5. Answers include source citations with document name, excerpt, and relevance score

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.14, FastAPI, SQLModel, Pydantic |
| Frontend | SvelteKit 5, TypeScript, Vite 8 |
| Database | PostgreSQL 18 with pgvector |
| Object Storage | AWS S3 |
| LLM | Claude Sonnet via Amazon Bedrock |
| Embeddings | Amazon Titan V2 via Bedrock |
| Infrastructure | Terraform (VPC, ECS Fargate, ALB, RDS, ECR) |
| CI/CD | GitHub Actions |

## Repository Structure

```
backend/        Python FastAPI REST API
frontend/       SvelteKit SPA (TypeScript)
terraform/      AWS infrastructure as code
sql/            Database table definitions
docs/           Specification and task tracking
```

See component documentation:

- [**Backend README**](backend/README.md) — API routes, architecture, environment variables, testing
- [**Frontend README**](frontend/README.md) — Pages, auth flow, stores, components

## Quick Start

### Full stack with Docker

```bash
docker compose up --build
```

This starts:
- **PostgreSQL** (pgvector) on port 5432
- **Backend** on port 8000
- **Frontend** on port 3000

Login with the default admin credentials: `admin` / `admin`.

### Local development

**Backend:**

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload    # :8000
```

**Frontend:**

```bash
cd frontend
npm run dev                      # :5173, proxies /api → :8000
```

### Database

Tables are created manually via SQL — apply `sql/table-definitions.sql` to PostgreSQL. The admin user is seeded automatically on backend startup.

## Deployment

Frontend and backend deploy as separate ECS Fargate services behind a shared ALB with path-based routing (`/api/*` to backend, `/*` to frontend). Same domain, no CORS.

All configuration is via environment variables — see [backend/README.md](backend/README.md) for the full list.
