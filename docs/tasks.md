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

- [ ] **2.1** Set up the database connection and schema (users, documents, document_chunks with pgvector)
- [ ] **2.2** User can log in with username and password and receive a session that auto-refreshes
- [ ] **2.3** User can log out
- [ ] **2.4** Admin user is seeded on first deployment
- [ ] **2.5** Admin can create a new user and receive a generated permanent password
- [ ] **2.6** Admin can list and delete users

## Epic 3: Document Upload & Management

> As a user, I can upload, view, and delete documents so that they are available for question answering.

### Stories

- [ ] **3.1** User can upload a document (PDF, TXT, CSV) which is stored in S3, chunked, embedded, and indexed in pgvector
- [ ] **3.2** User can list and view their uploaded documents
- [ ] **3.3** User can delete a document, removing it from S3 and the vector store
- [ ] **3.4** Users can only access their own documents

## Epic 4: RAG Question Answering

> As a user, I can ask natural language questions and receive answers grounded in my uploaded documents.

### Stories

- [ ] **4.1** User can ask a question and receive an AI-generated answer based on relevant document chunks
- [ ] **4.2** Answers include source citations with document name, excerpt, and relevance score
- [ ] **4.3** User is told when there is not enough information to answer the question

## Epic 5: Infrastructure

> As an operator, I can deploy the complete application stack to AWS using Terraform.

### Stories

- [x] **5.1** Provision networking (VPC, subnets, NAT gateway)
- [x] **5.2** Provision storage and registry (S3 bucket, ECR repositories)
- [x] **5.3** Provision database (RDS PostgreSQL with pgvector)
- [x] **5.4** Provision compute and load balancing (ECS Fargate, ALB with path-based routing)
- [ ] **5.5** Provision IAM roles with least-privilege access for ECS tasks
- [ ] **5.6** Wire all modules together and validate

## Epic 6: CI/CD

> As a developer, I get automated feedback on PRs and changes to main are automatically deployed.

### Stories

- [x] **6.1** Pull requests trigger automated linting, tests, and Terraform validation
- [x] **6.2** Merges to main build and push Docker images to ECR and deploy to ECS

## Epic 7: Testing & Documentation

> As a developer, I can run tests to verify the system works correctly and read documentation to understand the project.

### Stories

- [ ] **7.1** Backend has tests covering auth, admin, document management, and RAG
- [ ] **7.2** README documents project setup, local development, and deployment
