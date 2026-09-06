variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-1"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "kbqa"
}

variable "admin_username" {
  description = "Initial admin username"
  type        = string
  default     = "admin"
}

variable "admin_email" {
  description = "Initial admin email"
  type        = string
  default     = "admin@kbqa.local"
}

variable "bedrock_model_id" {
  description = "Bedrock model ID for LLM"
  type        = string
  default     = "anthropic.claude-sonnet-4-20250514-v1:0"
}

variable "bedrock_embedding_model_id" {
  description = "Bedrock model ID for embeddings"
  type        = string
  default     = "amazon.titan-embed-text-v2:0"
}
