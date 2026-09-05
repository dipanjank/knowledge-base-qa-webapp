resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["1c58a3a8518e8759bf075b76b750d4f2df264fcd"]

  tags = local.tags
}

data "aws_iam_policy_document" "deployment_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:dipanjank@23024451/knowledge-base-qa-webapp@1358142975:*"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "deployment" {
  name               = "${var.project_name}-deployment-role"
  assume_role_policy = data.aws_iam_policy_document.deployment_trust.json

  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "deployment_admin" {
  role       = aws_iam_role.deployment.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}
