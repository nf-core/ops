output "megatests_bucket" {
  value = {
    name   = aws_s3_bucket.nf_core_awsmegatests.bucket
    arn    = aws_s3_bucket.nf_core_awsmegatests.arn
    region = var.aws_region
  }
}

output "compute_env_ids" {
  value = { for k, v in seqera_compute_env.this : k => v.compute_env_id }
}

output "workspace_id" {
  value = local.workspace_id
}

output "towerforge_iam" {
  value = {
    user_name     = aws_iam_user.towerforge.name
    user_arn      = aws_iam_user.towerforge.arn
    access_key_id = aws_iam_access_key.towerforge.id
  }
}

output "towerforge_access_key_secret" {
  value     = aws_iam_access_key.towerforge.secret
  sensitive = true
}

output "github_credential" {
  value = {
    credential_name = seqera_credential.github_finegrained.name
    provider_type   = "github"
  }
}

output "deployment_method" {
  value = "opentofu"
}
