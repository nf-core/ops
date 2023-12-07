terraform {
  required_providers {
    github = {
      source  = "integrations/github"
      version = "5.42.0"
    }
  }
}

provider "github" {
  token = var.gh_token
  owner = var.org_name
}

# TODO
# module "pipelines" {
#   source = "./repos/piplines"
# }
