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

## Epic 5: Frontend — Authentication & Navigation

> As a user, I can log in through a web interface and navigate the application.

### Stories

- [ ] **5.1** User can log in and is redirected to the QA page; session persists across reloads
- [ ] **5.2** Unauthenticated users are redirected to the login page
- [ ] **5.3** Navigation bar shows links to Documents, QA, Logout (and Admin Users for admins)

## Epic 6: Frontend — Admin User Management

> As an admin, I can create, view, and delete users through the web interface.

### Stories

- [ ] **6.1** Admin can create a user and see the generated password displayed once
- [ ] **6.2** Admin can view a list of all users and delete non-admin users
- [ ] **6.3** Non-admin users cannot access the admin page

## Epic 7: Frontend — Document Management

> As a user, I can upload, browse, and delete documents through the web interface.

### Stories

- [ ] **7.1** User can upload a file via drag-and-drop or file picker with client-side validation
- [ ] **7.2** User can browse a paginated list of their documents and view document details
- [ ] **7.3** User can delete a document with a confirmation prompt

## Epic 8: Frontend — Question Answering

> As a user, I can ask questions in a chat interface and receive AI-generated answers with source citations.

### Stories

- [ ] **8.1** User can ask questions in a chat interface and see answers with source citations

## Epic 9: Infrastructure

> As an operator, I can deploy the complete application stack to AWS using Terraform.

### Stories

- [ ] **9.1** Provision networking (VPC, subnets, NAT gateway)
- [ ] **9.2** Provision storage and registry (S3 bucket, ECR repositories)
- [ ] **9.3** Provision database (RDS PostgreSQL with pgvector)
- [ ] **9.4** Provision compute and load balancing (ECS Fargate, ALB with path-based routing)
- [ ] **9.5** Provision IAM roles with least-privilege access for ECS tasks
- [ ] **9.6** Wire all modules together and validate

## Epic 10: CI/CD

> As a developer, I get automated feedback on PRs and changes to main are automatically deployed.

### Stories

- [ ] **10.1** Pull requests trigger automated linting, tests, and Terraform validation
- [ ] **10.2** Merges to main build and push Docker images to ECR and deploy to ECS

## Epic 11: Testing & Documentation

> As a developer, I can run tests to verify the system works correctly and read documentation to understand the project.

### Stories

- [ ] **11.1** Backend has tests covering auth, admin, document management, and RAG
- [ ] **11.2** README documents project setup, local development, and deployment
