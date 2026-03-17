resource "seqera_compute_env" "cpu" {
  workspace_id = local.workspace_id

  compute_env = {
    name           = "aws_ireland_fusionv2_nvme_cpu_snapshots"
    platform       = "aws-batch"
    credentials_id = seqera_credential.towerforge_aws.credentials_id
    description    = "CPU compute environment with Fusion v2 and NVMe storage"

    config = {
      aws_batch = {
        region                = var.aws_region
        work_dir              = local.s3_work_dir
        enable_wave           = true
        enable_fusion         = true
        nvme_storage_enabled = true
        fusion_snapshots      = true
        nextflow_config       = local.nextflow_cpu_config

        forge = merge(local.forge_defaults, {
          max_cpus       = 1000
          gpu_enabled    = false
          instance_types = ["c6id", "m6id", "r6id"]
          allow_buckets  = local.allow_buckets
          arm64_enabled  = false
        })
      }
    }
  }

  lifecycle {
    create_before_destroy = false
  }
}

resource "seqera_compute_env" "gpu" {
  workspace_id = local.workspace_id

  compute_env = {
    name           = "aws_ireland_fusionv2_nvme_gpu_snapshots"
    platform       = "aws-batch"
    credentials_id = seqera_credential.towerforge_aws.credentials_id
    description    = "GPU compute environment with Fusion v2 and NVMe storage"

    config = {
      aws_batch = {
        region                = var.aws_region
        work_dir              = local.s3_work_dir
        enable_wave           = true
        enable_fusion         = true
        nvme_storage_enabled = true
        fusion_snapshots      = true
        nextflow_config       = local.nextflow_gpu_config

        forge = merge(local.forge_defaults, {
          max_cpus       = 500
          gpu_enabled    = true
          instance_types = ["g4dn", "g5", "c6id", "m6id", "r6id"]
          allow_buckets  = local.allow_buckets
        })
      }
    }
  }

  lifecycle {
    create_before_destroy = false
  }
}

resource "seqera_compute_env" "arm" {
  workspace_id = local.workspace_id

  compute_env = {
    name           = "aws_ireland_fusionv2_nvme_cpu_ARM_snapshots"
    platform       = "aws-batch"
    credentials_id = seqera_credential.towerforge_aws.credentials_id
    description    = "ARM CPU compute environment with Fusion v2 and NVMe storage"

    config = {
      aws_batch = {
        region                = var.aws_region
        work_dir              = local.s3_work_dir
        enable_wave           = true
        enable_fusion         = true
        nvme_storage_enabled = true
        fusion_snapshots      = true
        nextflow_config       = local.nextflow_arm_config

        forge = merge(local.forge_defaults, {
          max_cpus       = 500
          gpu_enabled    = false
          instance_types = ["m6gd", "r6gd", "c6gd"]
          allow_buckets  = local.allow_buckets
          arm64_enabled  = true
        })
      }
    }
  }

  lifecycle {
    create_before_destroy = false
  }
}
