data "onepassword_item" "aws_megatests" {
  vault = var.op_vault
  title = "AWS megatests"
}

data "onepassword_item" "github_token" {
  vault = var.op_vault
  title = "GitHub nf-core PA Token Pulumi"
}

data "onepassword_item" "github_org_token" {
  vault = var.op_vault
  title = "GitHub nf-core Fine-Grained Token for Seqera Platform"
}

locals {
  # TOWER_ACCESS_TOKEN comes from env var (set by .envrc from 1Password custom field)
  platform_github_org_token = data.onepassword_item.github_org_token.password
  github_token              = data.onepassword_item.github_token.password
}
