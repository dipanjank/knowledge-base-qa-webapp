terraform {
  backend "s3" {
    bucket = "kbqa-terraform-state"
    key    = "statefiles/terraform.tfstate"
    region = "eu-west-1"
  }
}
