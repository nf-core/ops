terraform {
  required_providers {
    github = {
      source  = "integrations/github"
      version = "5.41.0"
    }
  }
}

provider "github" {
  token = var.gh_token
  owner = "nf-core"
}

# TODO
# module "pipelines" {
#   source = "./repos/piplines"
# }
