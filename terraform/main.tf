resource "random_password" "jwt_secret" {
  length  = 48
  special = false
}

resource "random_password" "admin" {
  length  = 24
  special = false
}

locals {
  tags = {
    Project        = var.project_name
    ManagedBy      = "terraform"
    RepositoryName = "knowledge-base-qa-webapp"
  }
  frontend_image_version = "0.1.0"
  backend_image_version  = "0.1.0"
}
