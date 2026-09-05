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
