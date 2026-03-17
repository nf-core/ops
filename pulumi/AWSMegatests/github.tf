resource "github_actions_organization_variable" "tower_compute_env_dev" {
  for_each      = local.compute_envs
  variable_name = "TOWER_COMPUTE_ENV_${upper(each.key)}_DEV"
  value         = seqera_compute_env.this[each.key].compute_env_id
  visibility    = "all"
}

resource "github_actions_organization_variable" "tower_workspace_id_dev" {
  variable_name = "TOWER_WORKSPACE_ID_DEV"
  value         = local.workspace_id
  visibility    = "all"
}

import {
  to = github_actions_organization_variable.aws_s3_bucket
  id = "AWS_S3_BUCKET"
}

resource "github_actions_organization_variable" "aws_s3_bucket" {
  variable_name = "AWS_S3_BUCKET"
  value         = aws_s3_bucket.nf_core_awsmegatests.bucket
  visibility    = "all"
}
