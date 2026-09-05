# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Knowledge Base QA Web Application — a fullstack app for uploading documents, indexing them into an Amazon Bedrock Knowledge Base, and performing RAG-based question answering.

## Repository Structure

Monorepo with three top-level directories:

- `backend/` — Python FastAPI REST API
- `frontend/` — SvelteKit web application
- `terraform/` — Infrastructure as Code (AWS)

## Tech Stack

- **Backend**: Python, FastAPI
- **Frontend**: SvelteKit (TypeScript)
- **Infrastructure**: Terraform (AWS ECS Fargate, ALB, S3, ECR, Bedrock)
- **CI/CD**: GitHub Actions → AWS ECR
- **Auth**: Username/password with JWT
