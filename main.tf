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
  owner = "Applied-Genomics-UTD"
}

resource "github_repository" "existing_repo" {
  name        = "repo0088"
  description = "This is my Github repository"
  visibility  = "private"
  auto_init   = true
}
