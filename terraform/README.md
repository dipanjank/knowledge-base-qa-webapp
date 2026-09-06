# Terraform — KBQA Infrastructure

AWS infrastructure for the Knowledge Base QA web application.

## Prerequisites

- Terraform >= 1.5
- AWS provider ~> 6.0
- AWS credentials with sufficient permissions

## State Management

State is stored remotely in S3:

| Setting | Value                          |
|---------|--------------------------------|
| Bucket  | `kbqa-terraform-state`         |
| Key     | `statefiles/terraform.tfstate` |
| Region  | `eu-west-1`                    |

The state bucket is itself managed by Terraform (`state_bucket.tf`) with versioning enabled and all public access blocked.

## Resources

### Networking (`vpc.tf`)

VPC created using [`terraform-aws-modules/vpc/aws`](https://registry.terraform.io/modules/terraform-aws-modules/vpc/aws) ~> 5.0:

| Resource                | Details                                   |
|-------------------------|-------------------------------------------|
| VPC CIDR                | `10.0.0.0/16`                             |
| Public subnets          | `10.0.1.0/24`, `10.0.2.0/24` (AZs a, b)   |
| Private subnets         | `10.0.10.0/24`, `10.0.11.0/24` (AZs a, b) |
| Database subnets        | `10.0.20.0/24`, `10.0.21.0/24` (AZs a, b) |
| Database subnet group   | Yes (for RDS)                              |
| Internet Gateway        | Yes (for public subnets)                  |
| NAT Gateway             | Single (shared by private subnets)        |
| DNS hostnames / support | Enabled                                   |

### SSM Parameters (`ssm.tf`)

Infrastructure and application outputs are published to SSM Parameter Store:

| Parameter                           | Type         | Description                        |
|-------------------------------------|--------------|------------------------------------|
| `/<project>/vpc/id`                 | String       | VPC ID                             |
| `/<project>/vpc/cidr`               | String       | VPC CIDR block                     |
| `/<project>/vpc/public-subnet-ids`  | StringList   | Comma-separated public subnet IDs  |
| `/<project>/vpc/private-subnet-ids` | StringList   | Comma-separated private subnet IDs |
| `/<project>/db/username`            | String       | Database master username           |
| `/<project>/db/password`            | SecureString | Database master password           |
| `/<project>/db/url`                 | SecureString | Full database connection URL       |
| `/<project>/s3/data-bucket-name`    | String       | Data bucket name                   |
| `/<project>/s3/data-bucket-arn`     | String       | Data bucket ARN                    |
| `/<project>/app/jwt-secret`         | SecureString | JWT signing secret                 |
| `/<project>/app/admin-username`     | String       | Initial admin username             |
| `/<project>/app/admin-password`     | SecureString | Initial admin password             |
| `/<project>/ecs/cluster-name`       | String       | ECS cluster name                   |
| `/<project>/ecs/cluster-arn`        | String       | ECS cluster ARN                    |
| `/<project>/alb/arn`                | String       | ALB ARN                            |
| `/<project>/alb/dns-name`          | String       | ALB DNS name                       |
| `/<project>/alb/http-listener-arn` | String       | ALB HTTP listener ARN              |
| `/<project>/alb/security-group-id` | String       | ALB security group ID              |

### RDS PostgreSQL (`rds.tf`)

PostgreSQL database using [`terraform-aws-modules/rds/aws`](https://registry.terraform.io/modules/terraform-aws-modules/rds/aws) ~> 6.0:

| Setting                 | Value                              |
|-------------------------|------------------------------------|
| Engine                  | PostgreSQL 17                      |
| Instance class          | `db.t4g.micro`                     |
| Storage                 | 10 GB (auto-scales to 20 GB)      |
| Multi-AZ                | No                                 |
| Backup retention        | 1 day                              |
| Deletion protection     | No                                 |
| Database name           | `kbqa`                             |
| Username                | `kbqa_admin`                       |
| Password                | Random 24-char alphanumeric        |
| Subnet group            | VPC database subnets               |
| Allowed extensions      | pgvector (`vector`)                |

**Security Group** — `kbqa-database-sg` allows inbound PostgreSQL (5432) from the VPC CIDR only.

### ECR Repositories (`ecr.tf`)

Container registries for application images:

| Repository | Description                    |
|------------|--------------------------------|
| `backend`  | Backend FastAPI application    |
| `frontend` | Frontend SvelteKit application |
| `rag`      | RAG worker service             |

All repositories have mutable tags, force delete enabled, and a lifecycle policy that keeps the last 5 images.

### GitHub OIDC (`oidc_github.tf`)

Keyless authentication for GitHub Actions via OIDC federation:

- **OIDC Provider** — `token.actions.githubusercontent.com`
- **Deployment Role** — `kbqa-deployment-role` with `AdministratorAccess`
- **Trust Policy** — scoped to the `dipanjank/knowledge-base-qa-webapp` repository (owner and repo IDs in the subject claim)

### ALB (`alb.tf`)

Internet-facing Application Load Balancer (`kbqa-alb`) in the public subnets. Routes traffic to Fargate tasks in the private subnets.

- **Security Group** — `kbqa-alb-sg` allows inbound HTTP (80) and HTTPS (443) from anywhere
- **HTTP Listener** — Forwards to the frontend target group by default
- **Backend Listener Rule** — Routes `/api/*`, `/docs`, `/openapi.json` to the backend target group (priority 100)
- **Backend Target Group** — IP-based target group on port 8000, health-checked on `/api/health`
- **Frontend Target Group** — IP-based target group on port 3000, health-checked on `/`

### ECS Cluster (`ecs_cluster.tf`)

`kbqa-cluster` with Fargate capacity provider and Container Insights enabled.

### Frontend Service (`ecs_frontend.tf`)

`kbqa-frontend` Fargate service (1 task, no autoscaling) using [`terraform-aws-modules/ecs/aws//modules/service`](https://registry.terraform.io/modules/terraform-aws-modules/ecs/aws) ~> 7.0, deployed to the private subnets:

| Setting    | Value                                  |
|------------|----------------------------------------|
| CPU        | 256 (0.25 vCPU)                        |
| Memory     | 512 MB                                 |
| Container  | `kbqa-frontend` ECR image on port 3000 |
| Logging    | CloudWatch (`/ecs/kbqa-frontend`, 7d)  |
| Networking | Private subnets, ALB ingress on 3000   |

### Backend Service (`ecs_backend.tf`)

`kbqa-backend` Fargate service (1 task, no autoscaling) using [`terraform-aws-modules/ecs/aws//modules/service`](https://registry.terraform.io/modules/terraform-aws-modules/ecs/aws) ~> 7.0, deployed to the private subnets:

| Setting     | Value                                                      |
|-------------|------------------------------------------------------------|
| CPU         | 512 (0.5 vCPU)                                            |
| Memory      | 1024 MB                                                    |
| Container   | `kbqa-backend` ECR image on port 8000                      |
| Environment | `AWS_REGION`, `S3_BUCKET_NAME`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`, `JWT_REFRESH_TOKEN_EXPIRE_DAYS`, `ADMIN_USERNAME`, `ADMIN_EMAIL` |
| Secrets     | `DATABASE_URL`, `JWT_SECRET`, `ADMIN_PASSWORD` from SSM    |
| Logging     | CloudWatch (`/ecs/kbqa-backend`, 7d)                       |
| Networking  | Private subnets, ALB ingress on 8000                       |

### RAG Worker Service (`ecs_rag.tf`)

`kbqa-rag` Fargate service (1 task, no autoscaling) using [`terraform-aws-modules/ecs/aws//modules/service`](https://registry.terraform.io/modules/terraform-aws-modules/ecs/aws) ~> 7.0, deployed to the private subnets:

| Setting     | Value                                                                        |
|-------------|------------------------------------------------------------------------------|
| CPU         | 1024 (1 vCPU)                                                                |
| Memory      | 2048 MB                                                                      |
| Container   | `kbqa-rag` ECR image (no port mappings — worker only)                        |
| Environment | `AWS_REGION`, `S3_BUCKET_NAME`, `SQS_QUEUE_URL`, `BEDROCK_EMBEDDING_MODEL_ID` |
| Secrets     | `DATABASE_URL` from SSM                                                      |
| IAM         | SQS (Receive/Delete), S3 (GetObject), Bedrock (InvokeModel)                 |
| Logging     | CloudWatch (`/ecs/kbqa-rag`, 7d)                                             |
| Networking  | Private subnets, egress only (no inbound traffic)                            |

### SQS Queues (`sqs.tf`)

| Queue            | Description                              | Settings                                          |
|------------------|------------------------------------------|----------------------------------------------------|
| `kbqa-rag`       | RAG job processing queue                 | 900s visibility, 1 day retention, 20s long poll    |
| `kbqa-rag-dlq`   | Dead-letter queue for failed RAG jobs    | 14 day retention, redrive after 3 failed attempts  |

### Data Bucket (`s3.tf`)

S3 bucket for document uploads (`kbqa-data`), created using [`terraform-aws-modules/s3-bucket/aws`](https://registry.terraform.io/modules/terraform-aws-modules/s3-bucket/aws) 5.15.4. Versioning enabled, all public access blocked. Bucket name and ARN are published to SSM Parameter Store.

### State Bucket (`state_bucket.tf`)

S3 bucket for Terraform remote state, created using [`terraform-aws-modules/s3-bucket/aws`](https://registry.terraform.io/modules/terraform-aws-modules/s3-bucket/aws) 5.15.4. Versioning enabled, all public access blocked.

## Variables

| Name                         | Description                  | Default                               |
|------------------------------|------------------------------|---------------------------------------|
| `aws_region`                 | AWS region                   | `eu-west-1`                           |
| `project_name`               | Project name for resources   | `kbqa`                                |
| `admin_username`             | Initial admin username       | `admin`                               |
| `admin_email`                | Initial admin email          | `admin@kbqa.local`                    |
| `bedrock_model_id`           | Bedrock LLM model ID        | `qwen.qwen3-next-80b-a3b` |
| `bedrock_embedding_model_id` | Bedrock embedding model ID   | `amazon.titan-embed-text-v2:0`        |

## Outputs

| Name                         | Description                               |
|------------------------------|-------------------------------------------|
| `state_bucket_name`          | Name of the S3 state bucket               |
| `state_bucket_arn`           | ARN of the S3 state bucket                |
| `deployment_role_arn`        | ARN of the GitHub Actions deployment role |
| `vpc_id`                     | ID of the VPC                             |
| `public_subnet_ids`          | IDs of the public subnets                 |
| `private_subnet_ids`         | IDs of the private subnets                |
| `rds_endpoint`               | Endpoint of the RDS instance              |
| `rds_port`                   | Port of the RDS instance                  |
| `database_security_group_id` | ID of the database security group         |
| `data_bucket_name`           | Name of the S3 data bucket                |
| `data_bucket_arn`            | ARN of the S3 data bucket                 |
| `ecs_cluster_name`           | Name of the ECS cluster                   |
| `ecs_cluster_arn`            | ARN of the ECS cluster                    |
| `alb_arn`                    | ARN of the ALB                            |
| `alb_dns_name`               | DNS name of the ALB                       |
| `alb_http_listener_arn`      | ARN of the ALB HTTP listener              |
| `alb_security_group_id`      | ID of the ALB security group              |
| `sqs_rag_queue_url`          | URL of the RAG SQS queue                  |
| `sqs_rag_queue_arn`          | ARN of the RAG SQS queue                  |
| `sqs_rag_dlq_url`           | URL of the RAG SQS dead-letter queue      |

## SSM Parameters

All parameters are prefixed with `/<project_name>/` (default: `/kbqa/`).

| Parameter                      | Type         | Value                              |
|--------------------------------|--------------|------------------------------------|
| `/kbqa/vpc/id`                 | String       | VPC ID                             |
| `/kbqa/vpc/cidr`               | String       | VPC CIDR block                     |
| `/kbqa/vpc/public-subnet-ids`  | StringList   | Comma-separated public subnet IDs  |
| `/kbqa/vpc/private-subnet-ids` | StringList   | Comma-separated private subnet IDs |
| `/kbqa/db/username`            | String       | Database master username           |
| `/kbqa/db/password`            | SecureString | Database master password           |
| `/kbqa/db/url`                 | SecureString | Full database connection URL       |
| `/kbqa/s3/data-bucket-name`   | String       | Data bucket name                   |
| `/kbqa/s3/data-bucket-arn`    | String       | Data bucket ARN                    |
| `/kbqa/app/jwt-secret`        | SecureString | JWT signing secret                 |
| `/kbqa/app/admin-username`    | String       | Initial admin username             |
| `/kbqa/app/admin-password`    | SecureString | Initial admin password             |
| `/kbqa/ecs/cluster-name`      | String       | ECS cluster name                   |
| `/kbqa/ecs/cluster-arn`       | String       | ECS cluster ARN                    |
| `/kbqa/alb/arn`               | String       | ALB ARN                            |
| `/kbqa/alb/dns-name`          | String       | ALB DNS name                       |
| `/kbqa/alb/http-listener-arn` | String       | ALB HTTP listener ARN              |
| `/kbqa/alb/security-group-id` | String       | ALB security group ID              |

## File Layout

```
terraform/
├── alb.tf              # Application Load Balancer and security group
├── backend.tf          # S3 remote state configuration
├── ecs_backend.tf      # ECS Fargate backend service
├── ecs_cluster.tf      # ECS Fargate cluster
├── ecs_frontend.tf     # ECS Fargate frontend service
├── ecs_rag.tf          # ECS Fargate RAG worker service
├── ecr.tf              # ECR repositories and lifecycle policies
├── main.tf             # Local values (tags, image versions) and generated secrets
├── oidc_github.tf      # GitHub OIDC provider and deployment role
├── outputs.tf          # Terraform outputs
├── providers.tf        # AWS provider configuration
├── rds.tf              # RDS PostgreSQL instance and security group
├── s3.tf               # S3 data bucket for document uploads
├── sqs.tf              # SQS queues for async RAG processing
├── ssm.tf              # SSM parameters for shared outputs
├── state_bucket.tf     # S3 state bucket
├── variables.tf        # Input variables
├── versions.tf         # Terraform and provider version constraints
└── vpc.tf              # VPC, subnets, IGW, NAT gateway
```

## CI/CD

The Terraform workflow (`.github/workflows/terraform.yml`) runs on changes to the `terraform/` directory:

- **All branches**: `fmt -check`, `init`, `validate`, `plan` (plan output is posted as a PR comment)
- **Main branch only**: `terraform apply -auto-approve` using the saved plan

Authentication uses OIDC — no static AWS credentials are stored in GitHub.
