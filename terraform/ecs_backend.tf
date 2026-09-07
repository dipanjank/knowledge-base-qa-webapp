module "backend_service" {
  source  = "terraform-aws-modules/ecs/aws//modules/service"
  version = "~> 7.0"

  name        = "${var.project_name}-backend"
  cluster_arn = aws_ecs_cluster.main.arn

  desired_count = 1

  cpu    = 512
  memory = 1024

  enable_autoscaling = false

  task_exec_ssm_param_arns = [
    aws_ssm_parameter.database_url.arn,
    aws_ssm_parameter.jwt_secret.arn,
    aws_ssm_parameter.admin_password.arn,
  ]

  tasks_iam_role_statements = [
    {
      effect    = "Allow"
      actions   = ["sqs:SendMessage"]
      resources = [aws_sqs_queue.rag.arn]
    },
  ]

  container_definitions = {
    backend = {
      essential = true
      image     = "${aws_ecr_repository.backend.repository_url}:${local.backend_image_version}"

      portMappings = [
        {
          name          = "http"
          containerPort = 8000
          hostPort      = 8000
          protocol      = "tcp"
        }
      ]

      readonlyRootFilesystem = false

      healthCheck = {
        command     = ["CMD-SHELL", "wget -qO- http://localhost:8000/api/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 30
      }

      environment = [
        { name = "AWS_REGION", value = var.aws_region },
        { name = "S3_BUCKET_NAME", value = module.data_bucket.s3_bucket_id },
        { name = "SQS_QUEUE_URL", value = aws_sqs_queue.rag.url },
        { name = "JWT_ACCESS_TOKEN_EXPIRE_MINUTES", value = "30" },
        { name = "JWT_REFRESH_TOKEN_EXPIRE_DAYS", value = "7" },
        { name = "ADMIN_USERNAME", value = var.admin_username },
        { name = "ADMIN_EMAIL", value = var.admin_email },
      ]

      secrets = [
        { name = "DATABASE_URL", valueFrom = aws_ssm_parameter.database_url.arn },
        { name = "JWT_SECRET", valueFrom = aws_ssm_parameter.jwt_secret.arn },
        { name = "ADMIN_PASSWORD", valueFrom = aws_ssm_parameter.admin_password.arn },
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/${var.project_name}-backend"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "backend"
        }
      }
    }
  }

  load_balancer = {
    service = {
      target_group_arn = aws_lb_target_group.backend.arn
      container_name   = "backend"
      container_port   = 8000
    }
  }

  subnet_ids = module.vpc.private_subnets

  security_group_ingress_rules = {
    alb = {
      from_port                    = 8000
      to_port                      = 8000
      ip_protocol                  = "tcp"
      referenced_security_group_id = aws_security_group.alb.id
    }
  }

  security_group_egress_rules = {
    all = {
      ip_protocol = "-1"
      cidr_ipv4   = "0.0.0.0/0"
    }
  }

  tags = local.tags
}

resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${var.project_name}-backend"
  retention_in_days = 7

  tags = local.tags
}
