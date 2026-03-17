provider "aws" {
  region = var.aws_region
}

provider "github" {
  token = local.github_token
  owner = var.github_owner
}

provider "seqera" {
  server_url = "https://api.cloud.seqera.io"
  # bearer_auth read from TOWER_ACCESS_TOKEN env var (set by .envrc)
}

provider "onepassword" {
  account = "nf-core"
}
