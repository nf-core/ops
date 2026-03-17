resource "seqera_credential" "github_finegrained" {
  name          = "nf-core-github-finegrained"
  description   = "Fine-grained GitHub token to avoid rate limits when Platform pulls pipeline repositories"
  provider_type = "github"
  workspace_id  = local.workspace_id

  keys = {
    github = {
      username = "nf-core-bot"
      password = local.platform_github_org_token
    }
  }
}
