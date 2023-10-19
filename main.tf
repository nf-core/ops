terraform {
  required_providers {
    github = {
      source  = "integrations/github"
      version = "5.40.0"
    }
  }
}

provider "github" {
  token = ""
  owner = "nf-core"
}

# TODO
# module "pipelines" {
#   source = "./repos/piplines"
# }
