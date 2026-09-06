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

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.main.arn
}
