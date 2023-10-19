# import {
#   to = github_repository.methylseq
#   id = "methylseq"
# }
# (imported from "methylseq")
resource "github_repository" "methylseq" {
  allow_auto_merge    = false
  allow_merge_commit  = true
  allow_rebase_merge  = true
  allow_squash_merge  = true
  allow_update_branch = false
  archived            = false
  auto_init           = false
  # FIXME [DEPRECATED] Use the github_branch_default resource instead
  default_branch         = "master"
  delete_branch_on_merge = false
  description            = "Methylation (Bisulfite-Sequencing) analysis pipeline using Bismark or bwa-meth + MethylDackel"
  # etag                        = "W/\"7e9059e572593f0b3393b312a565a1612d91a06fb9450a48a197f0425fd87cb9\""
  # full_name            = "nf-core/methylseq"
  has_discussions      = false
  has_downloads        = true
  has_issues           = true
  has_projects         = false
  has_wiki             = false
  homepage_url         = "https://nf-co.re/methylseq"
  is_template          = false
  merge_commit_message = "PR_TITLE"
  merge_commit_title   = "MERGE_MESSAGE"
  name                 = "methylseq"
  # primary_language     = "Nextflow"
  # repo_id                     = 124913037
  squash_merge_commit_message = "COMMIT_MESSAGES"
  squash_merge_commit_title   = "COMMIT_OR_PR_TITLE"
  topics = [
    "bisulfite-sequencing",
    "dna-methylation",
    "em-seq",
    "epigenome",
    "epigenomics",
    "methyl-seq",
    "nextflow",
    "nf-core",
    "pbat",
    "pipeline",
    "rrbs",
    "workflow",
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
