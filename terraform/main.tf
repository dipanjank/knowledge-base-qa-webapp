locals {
  tags = {
    Project        = var.project_name
    ManagedBy      = "terraform"
    RepositoryName = "knowledge-base-qa-webapp"
  }
}
