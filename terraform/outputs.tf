output "state_bucket_name" {
  description = "Name of the S3 state bucket"
  value       = module.state_bucket.s3_bucket_id
}

output "state_bucket_arn" {
  description = "ARN of the S3 state bucket"
  value       = module.state_bucket.s3_bucket_arn
}

output "deployment_role_arn" {
  description = "ARN of the GitHub Actions deployment role"
  value       = aws_iam_role.deployment.arn
}

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.vpc.public_subnets
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.vpc.private_subnets
}

output "rds_endpoint" {
  description = "Endpoint of the RDS instance"
  value       = module.rds.db_instance_endpoint
}

output "rds_port" {
  description = "Port of the RDS instance"
  value       = module.rds.db_instance_port
}

output "database_security_group_id" {
  description = "ID of the database security group"
  value       = aws_security_group.database.id
}

output "data_bucket_name" {
  description = "Name of the S3 data bucket"
  value       = module.data_bucket.s3_bucket_id
}

output "data_bucket_arn" {
  description = "ARN of the S3 data bucket"
  value       = module.data_bucket.s3_bucket_arn
}

output "alb_arn" {
  description = "ARN of the ALB"
  value       = aws_lb.main.arn
}

output "alb_dns_name" {
  description = "DNS name of the ALB"
  value       = aws_lb.main.dns_name
}

output "alb_http_listener_arn" {
  description = "ARN of the ALB HTTP listener"
  value       = aws_lb_listener.http.arn
}

output "alb_security_group_id" {
  description = "ID of the ALB security group"
  value       = aws_security_group.alb.id
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.main.arn
}

output "sqs_rag_queue_url" {
  description = "URL of the RAG SQS queue"
  value       = aws_sqs_queue.rag.url
}

output "sqs_rag_queue_arn" {
  description = "ARN of the RAG SQS queue"
  value       = aws_sqs_queue.rag.arn
}

output "sqs_rag_dlq_url" {
  description = "URL of the RAG SQS dead-letter queue"
  value       = aws_sqs_queue.rag_dlq.url
}
