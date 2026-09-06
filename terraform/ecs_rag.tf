module "rag_service" {
  source  = "terraform-aws-modules/ecs/aws//modules/service"
  version = "~> 7.0"

  name        = "${var.project_name}-rag"
  cluster_arn = aws_ecs_cluster.main.arn

  desired_count = 1

  cpu    = 1024
  memory = 2048

  enable_autoscaling = false

  # No load balancer — worker only
  assign_public_ip = false

  task_exec_ssm_param_arns = [
    aws_ssm_parameter.database_url.arn,
  ]

  tasks_iam_role_statements = [
    {
      effect = "Allow"
      actions = [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes",
      ]
      resources = [aws_sqs_queue.rag.arn]
    },
    {
      effect    = "Allow"
      actions   = ["s3:GetObject"]
      resources = ["${module.data_bucket.s3_bucket_arn}/*"]
    },
    {
      effect    = "Allow"
      actions   = ["bedrock:InvokeModel"]
      resources = ["arn:aws:bedrock:${var.aws_region}::foundation-model/${var.bedrock_embedding_model_id}"]
    },
  ]

  container_definitions = {
    rag = {
      essential = true
      image     = "${aws_ecr_repository.rag.repository_url}:${local.rag_image_version}"

      readonlyRootFilesystem = false

      environment = [
        { name = "AWS_REGION", value = var.aws_region },
        { name = "S3_BUCKET_NAME", value = module.data_bucket.s3_bucket_id },
        { name = "SQS_QUEUE_URL", value = aws_sqs_queue.rag.url },
        { name = "BEDROCK_EMBEDDING_MODEL_ID", value = var.bedrock_embedding_model_id },
      ]

      secrets = [
        { name = "DATABASE_URL", valueFrom = aws_ssm_parameter.database_url.arn },
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/${var.project_name}-rag"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "rag"
        }
      }
    }
  }

  subnet_ids = module.vpc.private_subnets

  # No inbound traffic needed — worker only
  security_group_ingress_rules = {}

  security_group_egress_rules = {
    all = {
      ip_protocol = "-1"
      cidr_ipv4   = "0.0.0.0/0"
    }
  }

  tags = local.tags
}

resource "aws_cloudwatch_log_group" "rag" {
  name              = "/ecs/${var.project_name}-rag"
  retention_in_days = 7

  tags = local.tags
}
