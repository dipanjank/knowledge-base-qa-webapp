# Development Tasks

## Epic 1: Project Setup

> As a developer, I can clone the repo and run the application locally so that I can start developing features.

### Stories

- [x] **1.1** Bootstrap the backend application
- [x] **1.2** Bootstrap the frontend application
- [x] **1.3** Create docker-compose to run the full stack locally

## Epic 2: Authentication & User Management

> As a user, I can log in securely. As an admin, I can create and manage user accounts.

### Stories

- [x] **2.1** Set up the database connection and schema (users, documents, document_chunks with pgvector)
- [x] **2.2** User can log in with username and password and receive a session that auto-refreshes
- [x] **2.3** User can log out
- [x] **2.4** Admin user is seeded on first deployment
- [x] **2.5** Admin can create a new user and receive a generated permanent password
- [x] **2.6** Admin can list and delete users

## Epic 3: Document Upload & Management

> As a user, I can upload, view, and delete TXT documents so that they are available for question answering.

### Stories

- [x] **3.1** User can upload a TXT document which is stored in S3, chunked, embedded, and indexed in pgvector
- [x] **3.2** User can list and view their uploaded documents
- [x] **3.3** User can delete a document, removing it from S3 and the vector store
- [x] **3.4** Users can only access their own documents

## Epic 4: Async RAG Pipeline

> As a user, I can upload up to 5 documents at once and track processing progress. A separate worker service handles text extraction, chunking, and embedding asynchronously.

### Stories

- [ ] **4.1** Create `rag_jobs` table and SQLModel model with status tracking (pending/processing/completed/part_completed/failed)
- [ ] **4.2** Add `rag_job_id` FK to documents table linking documents to their RAG job
- [ ] **4.3** Create RAG job schema, repository, service, and router (`GET /api/rag-jobs/active`, `GET /api/rag-jobs/`)
- [ ] **4.4** Create SQS service for sending messages from the backend
- [ ] **4.5** Rewrite document upload to accept up to 5 files, create a RAG job, upload all to S3, and send an SQS message
- [ ] **4.6** Enforce one active RAG job per user (unique partial index on rag_jobs)
- [ ] **4.7** Create `rag-service/` worker: SQS consumer that polls for jobs, processes each document (extract text, chunk, embed via Bedrock Titan V2, store chunks), and updates job/document status
- [ ] **4.8** Frontend: multi-file upload (up to 5 TXT files), job status panel with polling, disable upload while job is active
- [ ] **4.9** Frontend: RAG job history page (`/rag-jobs`)

## Epic 5: RAG Question Answering

> As a user, I can ask natural language questions and receive answers grounded in my uploaded documents.

### Stories

- [ ] **5.1** User can ask a question and receive an AI-generated answer based on relevant document chunks
- [ ] **5.2** Answers include source citations with document name, excerpt, and relevance score
- [ ] **5.3** User is told when there is not enough information to answer the question

## Epic 6: Infrastructure

> As an operator, I can deploy the complete application stack to AWS using Terraform.

### Stories

- [x] **6.1** Provision networking (VPC, subnets, NAT gateway)
- [x] **6.2** Provision storage and registry (S3 bucket, ECR repositories)
- [x] **6.3** Provision database (RDS PostgreSQL with pgvector)
- [x] **6.4** Provision compute and load balancing (ECS Fargate, ALB with path-based routing)
- [x] **6.5** Provision IAM roles with least-privilege access for ECS tasks
- [x] **6.6** Wire all modules together and validate
- [ ] **6.7** Provision SQS queue (kbqa-rag) with DLQ for async RAG processing
- [ ] **6.8** Provision ECR repository and ECS service for kbqa-rag worker (no ALB, polls SQS)
- [ ] **6.9** Add SQS SendMessage IAM policy to backend task role and SQS_QUEUE_URL env var
- [ ] **6.10** Add SQS Receive/Delete, S3 GetObject, Bedrock InvokeModel IAM policies to RAG worker task role

## Epic 7: CI/CD

> As a developer, I get automated feedback on PRs and changes to main are automatically deployed.

### Stories

- [x] **7.1** Pull requests trigger automated linting, tests, and Terraform validation
- [x] **7.2** Merges to main build and push Docker images to ECR and deploy to ECS
- [ ] **7.3** Add CI/CD workflow for rag-service (lint, test, build, push to kbqa-rag ECR repo)
- [ ] **7.4** Add SQS_QUEUE_URL to backend CI test environment

## Epic 8: Testing & Documentation

> As a developer, I can run tests to verify the system works correctly and read documentation to understand the project.

### Stories

- [ ] **8.1** Backend has tests covering auth, admin, document management, and RAG
- [ ] **8.2** README documents project setup, local development, and deployment
