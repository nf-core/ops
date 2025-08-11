"""Seqera Platform compute environment deployment using Seqera Terraform provider"""

import pulumi
import pulumi_seqera as seqera


def create_seqera_provider(config):
    """Create and configure the Seqera provider"""
    return seqera.Provider(
        "seqera-provider",
        bearer_auth=config["tower_access_token"],
        server_url="https://api.cloud.seqera.io",
    )


def create_compute_environment(
    provider,
    name: str,
    credentials_id: str,
    workspace_id: float,
    config_args: dict,
    description: str | None = None,
):
    """Create a Seqera compute environment using Terraform provider"""

    # Create the forge configuration for AWS Batch
    forge_config = seqera.ComputeEnvComputeEnvConfigAwsBatchForgeArgs(
        type=config_args.get("forge", {}).get("type", "SPOT"),
        min_cpus=config_args.get("forge", {}).get("minCpus", 0),
        max_cpus=config_args.get("forge", {}).get("maxCpus", 1000),
        gpu_enabled=config_args.get("forge", {}).get("gpuEnabled", False),
        instance_types=config_args.get("forge", {}).get("instanceTypes", []),
        subnets=config_args.get("forge", {}).get("subnets", []),
        security_groups=config_args.get("forge", {}).get("securityGroups", []),
        dispose_on_deletion=config_args.get("forge", {}).get("disposeOnDeletion", True),
        allow_buckets=config_args.get("forge", {}).get("allowBuckets", []),
        efs_create=config_args.get("forge", {}).get("efsCreate", False),
        ebs_boot_size=config_args.get("forge", {}).get("ebsBootSize", 50),
        fargate_head_enabled=config_args.get("forge", {}).get(
            "fargateHeadEnabled", True
        ),
        arm64_enabled=config_args.get("forge", {}).get("arm64Enabled", False),
    )

    # Create AWS Batch configuration
    aws_batch_config = seqera.ComputeEnvComputeEnvConfigAwsBatchArgs(
        region=config_args.get("region", "eu-west-1"),
        work_dir=config_args.get("workDir", "s3://nf-core-awsmegatests"),
        forge=forge_config,
        wave_enabled=config_args.get("waveEnabled", True),
        fusion2_enabled=config_args.get("fusion2Enabled", True),
        nvnme_storage_enabled=config_args.get("nvnmeStorageEnabled", True),
        fusion_snapshots=config_args.get("fusionSnapshots", True),
        nextflow_config=config_args.get("nextflowConfig", ""),
    )

    # Create the compute environment configuration
    compute_env_config = seqera.ComputeEnvComputeEnvConfigArgs(
        aws_batch=aws_batch_config
    )

    # Create the compute environment args
    compute_env_args = seqera.ComputeEnvComputeEnvArgs(
        name=name,
        platform="aws-batch",
        credentials_id=credentials_id,
        config=compute_env_config,
        description=description,
    )

    # Create the compute environment resource
    compute_env = seqera.ComputeEnv(
        name,
        compute_env=compute_env_args,
        workspace_id=workspace_id,
        opts=pulumi.ResourceOptions(provider=provider),
    )

    return compute_env


def deploy_seqera_environments_terraform(config, towerforge_credentials_id):
    """Deploy Seqera Platform compute environments using Terraform provider"""

    # Create Seqera provider
    provider = create_seqera_provider(config)

    # Read existing seqerakit configurations
    import json

    with open("seqerakit/current-env-cpu.json", "r") as f:
        cpu_config = json.load(f)
    with open("seqerakit/current-env-gpu.json", "r") as f:
        gpu_config = json.load(f)
    with open("seqerakit/current-env-cpu-arm.json", "r") as f:
        arm_config = json.load(f)

    workspace_id = float(config["tower_workspace_id"])

    # Create CPU compute environment
    cpu_env = create_compute_environment(
        provider=provider,
        name="aws_ireland_fusionv2_nvme_cpu_snapshots",
        credentials_id=towerforge_credentials_id,
        workspace_id=workspace_id,
        config_args=cpu_config,
        description="CPU compute environment with Fusion v2 and NVMe storage",
    )

    # Create GPU compute environment
    gpu_env = create_compute_environment(
        provider=provider,
        name="aws_ireland_fusionv2_nvme_gpu_snapshots",
        credentials_id=towerforge_credentials_id,
        workspace_id=workspace_id,
        config_args=gpu_config,
        description="GPU compute environment with Fusion v2 and NVMe storage",
    )

    # Create ARM compute environment
    arm_env = create_compute_environment(
        provider=provider,
        name="aws_ireland_fusionv2_nvme_cpu_ARM_snapshots",
        credentials_id=towerforge_credentials_id,
        workspace_id=workspace_id,
        config_args=arm_config,
        description="ARM CPU compute environment with Fusion v2 and NVMe storage",
    )

    return {
        "cpu_env": cpu_env,
        "gpu_env": gpu_env,
        "arm_env": arm_env,
        "provider": provider,
    }


def get_compute_environment_ids_terraform(terraform_resources):
    """Extract compute environment IDs from Terraform provider resources"""
    return {
        "cpu": terraform_resources["cpu_env"].compute_env_id,
        "gpu": terraform_resources["gpu_env"].compute_env_id,
        "arm": terraform_resources["arm_env"].compute_env_id,
    }
