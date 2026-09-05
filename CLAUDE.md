# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Knowledge Base QA Web Application — a fullstack app for uploading documents, chunking/embedding them with pgvector, and performing RAG-based question answering via Amazon Bedrock.

## Repository Structure

Monorepo with three top-level directories:

- `backend/` — Python FastAPI REST API
- `frontend/` — SvelteKit (TypeScript, SPA mode, adapter-node)
- `terraform/` — Infrastructure as Code (AWS)

## Tech Stack

- **Backend**: Python 3.14, FastAPI, SQLAlchemy, Pydantic
- **Frontend**: SvelteKit 5, TypeScript, Vite 8
- **Database**: PostgreSQL 18 with pgvector
- **Infrastructure**: Terraform (AWS ECS Fargate, ALB, S3, ECR, RDS)
- **CI/CD**: GitHub Actions → AWS ECR
- **Auth**: JWT (access token 30m + refresh token 7d httpOnly cookie)
- **Embeddings**: Amazon Titan V2 via Bedrock
- **LLM**: Claude Sonnet via Bedrock

## Development Commands

### Backend
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload          # Run dev server on :8000
pytest                                  # Run all tests
pytest tests/test_health.py -v          # Run a single test file
ruff check app/                         # Lint
```

### Frontend
```bash
cd frontend
npm run dev                             # Run dev server on :5173 (proxies /api to :8000)
npm run build                           # Production build
npm run check                           # Type check
```

### Full Stack (Docker)
```bash
docker compose up --build               # Backend :8000, Frontend :3000, PostgreSQL :5432
```

## Architecture Notes

- Database tables are created manually via SQL (no Alembic)
- Custom RAG pipeline: text extraction → chunking (500 tokens, 50 overlap) → Titan embeddings → pgvector cosine search → Claude LLM
- Admin-only user creation (no self-registration), permanent generated passwords
- Frontend proxies `/api` to backend in dev; ALB does path-based routing in production
