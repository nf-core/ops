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
  allow_auto_merge            = false
  allow_merge_commit          = true
  allow_rebase_merge          = true
  allow_squash_merge          = true
  allow_update_branch         = false
  archived                    = false
  auto_init                   = false
  default_branch              = "main"
  delete_branch_on_merge      = false
  etag                        = "W/\"5bbb8e3dc822b8ebeaa5581a5e3798af50ff6a7fa1036dbdd554466f2af68fe5\""
  full_name                   = "Applied-Genomics-UTD/.github"
  git_clone_url               = "git://github.com/Applied-Genomics-UTD/.github.git"
  has_discussions             = false
  has_downloads               = true
  has_issues                  = true
  has_projects                = true
  has_wiki                    = true
  html_url                    = "https://github.com/Applied-Genomics-UTD/.github"
  http_clone_url              = "https://github.com/Applied-Genomics-UTD/.github.git"
  id                          = ".github"
  is_template                 = false
  merge_commit_message        = "PR_TITLE"
  merge_commit_title          = "MERGE_MESSAGE"
  name                        = ".github"
  node_id                     = "R_kgDOHgSHaQ"
  private                     = false
  repo_id                     = 503613289
  squash_merge_commit_message = "COMMIT_MESSAGES"
  squash_merge_commit_title   = "COMMIT_OR_PR_TITLE"
  ssh_clone_url               = "git@github.com:Applied-Genomics-UTD/.github.git"
  svn_url                     = "https://github.com/Applied-Genomics-UTD/.github"
  topics                      = []
  vulnerability_alerts        = false

  security_and_analysis {
    secret_scanning {
      status = "disabled"
    }
    secret_scanning_push_protection {
      status = "disabled"
    }
  }
}
