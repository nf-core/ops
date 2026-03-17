locals {
  workspace_id = seqera_workspace.dev.id

  nextflow_base_config = file("configs/nextflow-base.config")

  # Merge base config with env-specific config (stripping includeConfig lines)
  nextflow_cpu_config = "${local.nextflow_base_config}\n\n${replace(file("configs/nextflow-cpu.config"), "/includeConfig.*/", "")}"
  nextflow_gpu_config = "${local.nextflow_base_config}\n\n${replace(file("configs/nextflow-gpu.config"), "/includeConfig.*/", "")}"
  nextflow_arm_config = "${local.nextflow_base_config}\n\n${replace(file("configs/nextflow-arm.config"), "/includeConfig.*/", "")}"

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
}
