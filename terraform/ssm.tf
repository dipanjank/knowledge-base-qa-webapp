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

resource "aws_ssm_parameter" "alb_arn" {
  name  = "/${var.project_name}/alb/arn"
  type  = "String"
  value = aws_lb.main.arn

  tags = local.tags
}

resource "aws_ssm_parameter" "alb_dns_name" {
  name  = "/${var.project_name}/alb/dns-name"
  type  = "String"
  value = aws_lb.main.dns_name

  tags = local.tags
}

resource "aws_ssm_parameter" "alb_listener_arn" {
  name  = "/${var.project_name}/alb/http-listener-arn"
  type  = "String"
  value = aws_lb_listener.http.arn

  tags = local.tags
}

resource "aws_ssm_parameter" "alb_security_group_id" {
  name  = "/${var.project_name}/alb/security-group-id"
  type  = "String"
  value = aws_security_group.alb.id

  tags = local.tags
}

resource "aws_ssm_parameter" "ecs_cluster_name" {
  name  = "/${var.project_name}/ecs/cluster-name"
  type  = "String"
  value = aws_ecs_cluster.main.name

  tags = local.tags
}

resource "aws_ssm_parameter" "ecs_cluster_arn" {
  name  = "/${var.project_name}/ecs/cluster-arn"
  type  = "String"
  value = aws_ecs_cluster.main.arn

  tags = local.tags
}
