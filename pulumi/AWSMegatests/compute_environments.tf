resource "seqera_compute_env" "this" {
  for_each     = local.compute_envs
  workspace_id = local.workspace_id

  compute_env = {
    name           = each.value.name
    platform       = "aws-batch"
    credentials_id = seqera_credential.towerforge_aws.credentials_id
    description    = each.value.description

    config = {
      aws_batch = {
        region               = var.aws_region
        work_dir             = local.s3_work_dir
        enable_wave          = true
        enable_fusion        = true
        nvme_storage_enabled = true
        fusion_snapshots     = true
        nextflow_config      = local.nextflow_configs[each.key]

        forge = merge(local.forge_defaults, {
          max_cpus       = each.value.max_cpus
          gpu_enabled    = each.value.gpu_enabled
          arm64_enabled  = each.value.arm64_enabled
          instance_types = each.value.instance_types
          allow_buckets  = local.allow_buckets
        })
      }
    }
  }

  lifecycle {
    create_before_destroy = false
  }
}
