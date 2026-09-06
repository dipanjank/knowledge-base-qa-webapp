resource "aws_ssm_parameter" "vpc_id" {
  name  = "/${var.project_name}/vpc/id"
  type  = "String"
  value = module.vpc.vpc_id

  tags = local.tags
}

resource "aws_ssm_parameter" "vpc_cidr" {
  name  = "/${var.project_name}/vpc/cidr"
  type  = "String"
  value = module.vpc.vpc_cidr_block

  tags = local.tags
}

resource "aws_ssm_parameter" "public_subnet_ids" {
  name  = "/${var.project_name}/vpc/public-subnet-ids"
  type  = "StringList"
  value = join(",", module.vpc.public_subnets)

  tags = local.tags
}

resource "aws_ssm_parameter" "private_subnet_ids" {
  name  = "/${var.project_name}/vpc/private-subnet-ids"
  type  = "StringList"
  value = join(",", module.vpc.private_subnets)

  tags = local.tags
}

resource "aws_ssm_parameter" "db_username" {
  name  = "/${var.project_name}/db/username"
  type  = "String"
  value = module.rds.db_instance_username

  tags = local.tags
}

resource "aws_ssm_parameter" "db_password" {
  name  = "/${var.project_name}/db/password"
  type  = "SecureString"
  value = random_password.db.result

  tags = local.tags
}

resource "aws_ssm_parameter" "data_bucket_name" {
  name  = "/${var.project_name}/s3/data-bucket-name"
  type  = "String"
  value = module.data_bucket.s3_bucket_id

  tags = local.tags
}

resource "aws_ssm_parameter" "data_bucket_arn" {
  name  = "/${var.project_name}/s3/data-bucket-arn"
  type  = "String"
  value = module.data_bucket.s3_bucket_arn

  tags = local.tags
}
