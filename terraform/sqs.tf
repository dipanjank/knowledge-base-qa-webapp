resource "aws_sqs_queue" "rag_dlq" {
  name                      = "${var.project_name}-rag-dlq"
  message_retention_seconds = 1209600 # 14 days

  tags = local.tags
}

resource "aws_sqs_queue" "rag" {
  name                       = "${var.project_name}-rag"
  visibility_timeout_seconds = 900
  message_retention_seconds  = 86400 # 1 day
  receive_wait_time_seconds  = 20

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.rag_dlq.arn
    maxReceiveCount     = 3
  })

  tags = local.tags
}
