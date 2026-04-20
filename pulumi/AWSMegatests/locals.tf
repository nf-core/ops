locals {
  workspace_id = seqera_workspace.dev.id

  nextflow_base_config = file("configs/nextflow-base.config")

  s3_bucket_name = "nf-core-awsmegatests"
  s3_work_dir    = "s3://${local.s3_bucket_name}"
  allow_buckets  = ["s3://ngi-igenomes", "s3://${local.s3_bucket_name}", "s3://annotation-cache/"]

  # Shared forge defaults
  forge_defaults = {
    type                 = "SPOT"
    min_cpus             = 0
    subnets              = []
    security_groups      = []
    dispose_on_deletion  = true
    efs_create           = false
    ebs_boot_size        = 50
    fargate_head_enabled = true
  }

  # Compute environment variants — only differences from forge_defaults
  compute_envs = {
    cpu = {
      name           = "aws_ireland_fusionv2_nvme_cpu_snapshots"
      description    = "CPU compute environment with Fusion v2 and NVMe storage"
      max_cpus       = 1000
      gpu_enabled    = false
      arm64_enabled  = false
      instance_types = ["c6id", "m6id", "r6id"]
    }
    gpu = {
      name           = "aws_ireland_fusionv2_nvme_gpu_snapshots"
      description    = "GPU compute environment with Fusion v2 and NVMe storage"
      max_cpus       = 500
      gpu_enabled    = true
      arm64_enabled  = false
      instance_types = ["g4dn", "g5", "c6id", "m6id", "r6id"]
    }
    arm = {
      name           = "aws_ireland_fusionv2_nvme_cpu_ARM_snapshots"
      description    = "ARM CPU compute environment with Fusion v2 and NVMe storage"
      max_cpus       = 500
      gpu_enabled    = false
      arm64_enabled  = true
      instance_types = ["m6gd", "r6gd", "c6gd"]
    }
  }

  # Merge base config with env-specific config (stripping includeConfig lines)
  nextflow_configs = {
    for env, _ in local.compute_envs :
    env => "${local.nextflow_base_config}\n\n${replace(file("configs/nextflow-${env}.config"), "/includeConfig.*/", "")}"
  }
}
