# Terraform — KBQA Infrastructure

AWS infrastructure for the Knowledge Base QA web application.

## Prerequisites

- Terraform >= 1.5
- AWS provider ~> 6.0
- AWS credentials with sufficient permissions

## State Management

State is stored remotely in S3:

| Setting | Value |
|---------|-------|
| Bucket  | `kbqa-terraform-state` |
| Key     | `statefiles/terraform.tfstate` |
| Region  | `eu-west-1` |

The state bucket is itself managed by Terraform (`state_bucket.tf`) with versioning enabled and all public access blocked.

## Resources

### Networking (`vpc.tf`)

VPC created using [`terraform-aws-modules/vpc/aws`](https://registry.terraform.io/modules/terraform-aws-modules/vpc/aws) ~> 5.0:

| Resource | Details |
|----------|---------|
| VPC CIDR | `10.0.0.0/16` |
| Public subnets | `10.0.1.0/24`, `10.0.2.0/24` (AZs a, b) |
| Private subnets | `10.0.10.0/24`, `10.0.11.0/24` (AZs a, b) |
| Internet Gateway | Yes (for public subnets) |
| NAT Gateway | Single (shared by private subnets) |
| DNS hostnames / support | Enabled |

### SSM Parameters (`ssm.tf`)

VPC outputs are published to SSM Parameter Store for consumption by other services:

| Parameter | Type | Description |
|-----------|------|-------------|
| `/<project>/vpc/id` | String | VPC ID |
| `/<project>/vpc/public-subnet-ids` | StringList | Comma-separated public subnet IDs |
| `/<project>/vpc/private-subnet-ids` | StringList | Comma-separated private subnet IDs |

### GitHub OIDC (`oidc_github.tf`)

Keyless authentication for GitHub Actions via OIDC federation:

- **OIDC Provider** — `token.actions.githubusercontent.com`
- **Deployment Role** — `kbqa-deployment-role` with `AdministratorAccess`
- **Trust Policy** — scoped to the `dipanjank/knowledge-base-qa-webapp` repository (owner and repo IDs in the subject claim)

### State Bucket (`state_bucket.tf`)

S3 bucket for Terraform remote state, created using [`terraform-aws-modules/s3-bucket/aws`](https://registry.terraform.io/modules/terraform-aws-modules/s3-bucket/aws) 5.15.4. Versioning enabled, all public access blocked.

## Variables

| Name | Description | Default |
|------|-------------|---------|
| `aws_region` | AWS region | `eu-west-1` |
| `project_name` | Project name used for resource naming | `kbqa` |

## Outputs

| Name | Description |
|------|-------------|
| `state_bucket_name` | Name of the S3 state bucket |
| `state_bucket_arn` | ARN of the S3 state bucket |
| `deployment_role_arn` | ARN of the GitHub Actions deployment role |
| `vpc_id` | ID of the VPC |
| `public_subnet_ids` | IDs of the public subnets |
| `private_subnet_ids` | IDs of the private subnets |

## File Layout

```
terraform/
├── backend.tf          # S3 remote state configuration
├── main.tf             # Local values (tags)
├── oidc_github.tf      # GitHub OIDC provider and deployment role
├── outputs.tf          # Terraform outputs
├── providers.tf        # AWS provider configuration
├── ssm.tf              # SSM parameters for VPC outputs
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
