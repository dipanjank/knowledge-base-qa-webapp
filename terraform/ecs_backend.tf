module "backend_service" {
  source  = "terraform-aws-modules/ecs/aws//modules/service"
  version = "~> 7.0"

  name        = "${var.project_name}-backend"
  cluster_arn = aws_ecs_cluster.main.arn

  cpu    = 512
  memory = 1024

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
        command     = ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/health')\" || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 30
      }

      environment = [
        { name = "DATABASE_HOST", value = module.rds.db_instance_address },
        { name = "DATABASE_PORT", value = tostring(module.rds.db_instance_port) },
        { name = "DATABASE_NAME", value = var.project_name },
        { name = "DATABASE_USER", value = "${var.project_name}_admin" },
        { name = "AWS_DEFAULT_REGION", value = var.aws_region },
        { name = "S3_BUCKET_NAME", value = module.data_bucket.s3_bucket_id },
      ]

      secrets = [
        {
          name      = "DATABASE_PASSWORD"
          valueFrom = aws_ssm_parameter.db_password.arn
        }
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
