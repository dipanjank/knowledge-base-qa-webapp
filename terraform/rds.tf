resource "random_password" "db" {
  length  = 24
  special = false
}

resource "aws_security_group" "database" {
  name        = "${var.project_name}-database-sg"
  description = "Allow inbound access to the database from the VPC"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "PostgreSQL from VPC"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [module.vpc.vpc_cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.tags
}

module "rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"

  identifier = "${var.project_name}-db"

  engine               = "postgres"
  engine_version       = "17"
  family               = "postgres17"
  major_engine_version = "17"
  instance_class       = "db.t4g.micro"

  allocated_storage     = 10
  max_allocated_storage = 20

  db_name  = var.project_name
  username = "${var.project_name}_admin"
  port     = 5432

  manage_master_user_password = false
  password                    = random_password.db.result

  multi_az               = false
  db_subnet_group_name   = module.vpc.database_subnet_group_name
  vpc_security_group_ids = [aws_security_group.database.id]

  backup_retention_period = 1
  skip_final_snapshot     = true
  deletion_protection     = false

  parameters = [
    {
      name         = "rds.allowed_extensions"
      value        = "vector"
      apply_method = "pending-reboot"
    }
  ]

  performance_insights_enabled = false
  create_cloudwatch_log_group  = false

  tags = local.tags
}
