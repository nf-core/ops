# import {
#   to = github_repository.modules
#   id = "modules"
# }

resource "github_repository" "modules" {
  allow_auto_merge            = false
  allow_merge_commit          = false
  allow_rebase_merge          = false
  allow_squash_merge          = true
  allow_update_branch         = true
  archived                    = false
  auto_init                   = false
  default_branch              = "master"
  delete_branch_on_merge      = false
  description                 = "Repository to host tool-specific module files for the Nextflow DSL2 community!"
  has_discussions             = false
  has_downloads               = true
  has_issues                  = true
  has_projects                = true
  has_wiki                    = false
  homepage_url                = "https://nf-co.re"
  is_template                 = false
  merge_commit_message        = "PR_TITLE"
  merge_commit_title          = "MERGE_MESSAGE"
  name                        = "modules"
  squash_merge_commit_message = "COMMIT_MESSAGES"
  squash_merge_commit_title   = "PR_TITLE"
  topics = [
    "dsl2",
    "modules",
    "nextflow",
    "nf-core",
    "nf-test",
    "pipelines",
    "workflows",
  ]
  visibility           = "public"
  vulnerability_alerts = true

  security_and_analysis {
    secret_scanning {
      status = "disabled"
    }
    secret_scanning_push_protection {
      status = "disabled"
    }
  }
}
