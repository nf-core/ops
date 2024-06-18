terraform {
  required_providers {
    github = {
      source  = "integrations/github"
      version = "6.2.2"
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
