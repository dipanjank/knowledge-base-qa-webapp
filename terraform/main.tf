locals {
  tags = {
    Project        = var.project_name
    ManagedBy      = "terraform"
    RepositoryName = "knowledge-base-qa-webapp"
  }
  frontend_image_version = "0.1.0"
  backend_image_version  = "0.1.0"
}
