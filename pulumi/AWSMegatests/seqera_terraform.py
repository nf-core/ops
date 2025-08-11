"""Seqera Platform compute environment deployment using Seqera Terraform provider"""

import pulumi
import pulumi_seqera as seqera
import json
import os


def create_seqera_provider(config):
    """Create and configure the Seqera provider with error handling"""

    # Validate required configuration
    if not config.get("tower_access_token"):
        raise ValueError(
            "TOWER_ACCESS_TOKEN is required for Seqera provider. "
            "Please ensure it's set in your ESC environment with proper permissions: "
            "WORKSPACE_ADMIN or COMPUTE_ENV_ADMIN scope."
        )

    pulumi.log.info("Creating Seqera provider with Cloud API endpoint")

    try:
        return seqera.Provider(
            "seqera-provider",
            bearer_auth=config["tower_access_token"],
            server_url="https://api.cloud.seqera.io",
        )
    except Exception as e:
        pulumi.log.error(f"Failed to create Seqera provider: {e}")
        raise RuntimeError(
            f"Seqera provider initialization failed: {e}. "
            "This usually indicates token permissions issues. "
            "Ensure your TOWER_ACCESS_TOKEN has WORKSPACE_ADMIN or COMPUTE_ENV_ADMIN permissions."
        )


def create_compute_environment(
    provider,
    name: str,
    credentials_id: str,
    workspace_id: float,
    config_args: dict,
    description: str | None = None,
):
    """Create a Seqera compute environment using Terraform provider with error handling"""

    pulumi.log.info(f"Creating compute environment: {name}")

    # Validate input parameters
    if not name or not credentials_id:
        raise ValueError(f"Missing required parameters for compute environment {name}")

    if not config_args:
        raise ValueError(
            f"Configuration arguments are required for compute environment {name}"
        )

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

    # Create the compute environment resource with error handling
    try:
        compute_env = seqera.ComputeEnv(
            name,
            compute_env=compute_env_args,
            workspace_id=workspace_id,
            opts=pulumi.ResourceOptions(
                provider=provider,
                # Add custom timeout for compute environment creation
                custom_timeouts=pulumi.CustomTimeouts(
                    create="10m", update="10m", delete="5m"
                ),
            ),
        )

        pulumi.log.info(f"Successfully created compute environment: {name}")
        return compute_env

    except Exception as e:
        error_msg = (
            f"Failed to create compute environment '{name}': {e}. "
            "Common causes: "
            "1. Seqera API token lacks required permissions (403 Forbidden) "
            "2. Invalid credentials_id reference "
            "3. Workspace access restrictions "
            "4. Network connectivity issues"
        )
        pulumi.log.error(error_msg)
        raise RuntimeError(error_msg)


def deploy_seqera_environments_terraform(config, towerforge_credentials_id):
    """Deploy Seqera Platform compute environments using Terraform provider with comprehensive error handling"""

    pulumi.log.info(
        "Starting Seqera compute environment deployment using Terraform provider"
    )

    # Create Seqera provider with error handling
    try:
        provider = create_seqera_provider(config)
    except Exception as e:
        pulumi.log.error(f"Failed to create Seqera provider: {e}")
        raise

    # Read existing seqerakit configurations with error handling
    def load_config_file(filename):
        """Load configuration file with error handling"""
        try:
            if not os.path.exists(filename):
                raise FileNotFoundError(f"Configuration file not found: {filename}")

            with open(filename, "r") as f:
                config_data = json.load(f)

            pulumi.log.info(f"Successfully loaded configuration from {filename}")
            return config_data

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file {filename}: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration file {filename}: {e}")

    # Load all configuration files
    try:
        cpu_config = load_config_file("seqerakit/current-env-cpu.json")
        gpu_config = load_config_file("seqerakit/current-env-gpu.json")
        arm_config = load_config_file("seqerakit/current-env-cpu-arm.json")
    except Exception as e:
        pulumi.log.error(f"Configuration loading failed: {e}")
        raise

    # Validate workspace ID
    try:
        workspace_id = float(config["tower_workspace_id"])
        pulumi.log.info(f"Using workspace ID: {workspace_id}")
    except (ValueError, KeyError) as e:
        raise ValueError(f"Invalid or missing workspace ID: {e}")

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
