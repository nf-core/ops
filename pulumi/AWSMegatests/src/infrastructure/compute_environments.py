"""Seqera Platform compute environment deployment using Seqera Terraform provider."""

import json
import os
from typing import Dict, Any, Optional

import pulumi
import pulumi_seqera as seqera

from ..utils.constants import (
    COMPUTE_ENV_NAMES,
    COMPUTE_ENV_DESCRIPTIONS,
    CONFIG_FILES,
    DEFAULT_COMPUTE_ENV_CONFIG,
    DEFAULT_FORGE_CONFIG,
    TIMEOUTS,
    ERROR_MESSAGES,
)


class ComputeEnvironmentError(Exception):
    """Exception raised when compute environment operations fail."""

    pass


class ConfigurationError(Exception):
    """Exception raised when configuration loading fails."""

    pass


def load_config_file(filename: str) -> Dict[str, Any]:
    """Load configuration file with comprehensive error handling.

    Args:
        filename: Path to the JSON configuration file

    Returns:
        Dict[str, Any]: Loaded configuration data

    Raises:
        ConfigurationError: If file loading or parsing fails
    """
    try:
        if not os.path.exists(filename):
            raise FileNotFoundError(
                ERROR_MESSAGES["config_file_not_found"].format(filename)
            )

        with open(filename, "r") as f:
            config_data = json.load(f)

        pulumi.log.info(f"Successfully loaded configuration from {filename}")
        return config_data

    except json.JSONDecodeError as e:
        error_msg = ERROR_MESSAGES["invalid_json"].format(filename, e)
        raise ConfigurationError(error_msg) from e
    except Exception as e:
        error_msg = ERROR_MESSAGES["config_load_failed"].format(filename, e)
        raise ConfigurationError(error_msg) from e


def create_forge_config(
    config_args: Dict[str, Any],
) -> seqera.ComputeEnvComputeEnvConfigAwsBatchForgeArgs:
    """Create forge configuration for AWS Batch compute environment.

    Args:
        config_args: Configuration arguments from JSON file

    Returns:
        seqera.ComputeEnvComputeEnvConfigAwsBatchForgeArgs: Forge configuration
    """
    forge_data = config_args.get("forge", {})

    return seqera.ComputeEnvComputeEnvConfigAwsBatchForgeArgs(
        type=forge_data.get("type", DEFAULT_FORGE_CONFIG["type"]),
        min_cpus=forge_data.get("minCpus", DEFAULT_FORGE_CONFIG["minCpus"]),
        max_cpus=forge_data.get("maxCpus", DEFAULT_FORGE_CONFIG["maxCpus"]),
        gpu_enabled=forge_data.get("gpuEnabled", DEFAULT_FORGE_CONFIG["gpuEnabled"]),
        instance_types=forge_data.get(
            "instanceTypes", DEFAULT_FORGE_CONFIG["instanceTypes"]
        ),
        subnets=forge_data.get("subnets", DEFAULT_FORGE_CONFIG["subnets"]),
        security_groups=forge_data.get(
            "securityGroups", DEFAULT_FORGE_CONFIG["securityGroups"]
        ),
        dispose_on_deletion=forge_data.get(
            "disposeOnDeletion", DEFAULT_FORGE_CONFIG["disposeOnDeletion"]
        ),
        allow_buckets=forge_data.get(
            "allowBuckets", DEFAULT_FORGE_CONFIG["allowBuckets"]
        ),
        efs_create=forge_data.get("efsCreate", DEFAULT_FORGE_CONFIG["efsCreate"]),
        ebs_boot_size=forge_data.get(
            "ebsBootSize", DEFAULT_FORGE_CONFIG["ebsBootSize"]
        ),
        fargate_head_enabled=forge_data.get(
            "fargateHeadEnabled", DEFAULT_FORGE_CONFIG["fargateHeadEnabled"]
        ),
        arm64_enabled=forge_data.get(
            "arm64Enabled", DEFAULT_FORGE_CONFIG["arm64Enabled"]
        ),
    )


def create_compute_environment(
    provider: seqera.Provider,
    name: str,
    credentials_id: str,
    workspace_id: float,
    config_args: Dict[str, Any],
    description: Optional[str] = None,
) -> seqera.ComputeEnv:
    """Create a Seqera compute environment using Terraform provider with error handling.

    Args:
        provider: Configured Seqera provider instance
        name: Name for the compute environment
        credentials_id: Seqera credentials ID
        workspace_id: Seqera workspace ID
        config_args: Configuration arguments from JSON file
        description: Optional description for the compute environment

    Returns:
        seqera.ComputeEnv: Created compute environment resource

    Raises:
        ComputeEnvironmentError: If compute environment creation fails
        ValueError: If required parameters are missing
    """
    pulumi.log.info(f"Creating compute environment: {name}")

    # Validate input parameters
    if not name or not credentials_id:
        raise ValueError(ERROR_MESSAGES["missing_compute_env_params"].format(name))

    if not config_args:
        raise ValueError(ERROR_MESSAGES["missing_config_args"].format(name))

    # Create the forge configuration
    forge_config = create_forge_config(config_args)

    # Create AWS Batch configuration
    aws_batch_config = seqera.ComputeEnvComputeEnvConfigAwsBatchArgs(
        region=config_args.get("region", DEFAULT_COMPUTE_ENV_CONFIG["region"]),
        work_dir=config_args.get("workDir", DEFAULT_COMPUTE_ENV_CONFIG["workDir"]),
        forge=forge_config,
        wave_enabled=config_args.get(
            "waveEnabled", DEFAULT_COMPUTE_ENV_CONFIG["waveEnabled"]
        ),
        fusion2_enabled=config_args.get(
            "fusion2Enabled", DEFAULT_COMPUTE_ENV_CONFIG["fusion2Enabled"]
        ),
        nvnme_storage_enabled=config_args.get(
            "nvnmeStorageEnabled", DEFAULT_COMPUTE_ENV_CONFIG["nvnmeStorageEnabled"]
        ),
        fusion_snapshots=config_args.get(
            "fusionSnapshots", DEFAULT_COMPUTE_ENV_CONFIG["fusionSnapshots"]
        ),
        nextflow_config=config_args.get(
            "nextflowConfig", DEFAULT_COMPUTE_ENV_CONFIG["nextflowConfig"]
        ),
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
                # Force delete before replace to avoid name conflicts
                delete_before_replace=True,
                # Add custom timeout for compute environment creation
                custom_timeouts=pulumi.CustomTimeouts(
                    create=TIMEOUTS["compute_env_create"],
                    update=TIMEOUTS["compute_env_update"],
                    delete=TIMEOUTS["compute_env_delete"],
                ),
            ),
        )

        pulumi.log.info(f"Successfully created compute environment: {name}")
        return compute_env

    except Exception as e:
        error_msg = ERROR_MESSAGES["compute_env_create_failed"].format(name, e)
        pulumi.log.error(error_msg)
        raise ComputeEnvironmentError(error_msg) from e


def deploy_seqera_environments_terraform(
    config: Dict[str, Any],
    towerforge_credentials_id: str,
    seqera_provider: Optional[seqera.Provider] = None,
) -> Dict[str, Any]:
    """Deploy Seqera Platform compute environments using Terraform provider.

    Args:
        config: Configuration dictionary
        towerforge_credentials_id: Dynamic TowerForge credentials ID
        seqera_provider: Optional existing Seqera provider instance

    Returns:
        Dict[str, Any]: Dictionary containing created compute environments and provider

    Raises:
        ConfigurationError: If configuration loading fails
        ComputeEnvironmentError: If compute environment creation fails
        ValueError: If workspace ID is invalid
    """
    pulumi.log.info(
        "Starting Seqera compute environment deployment using Terraform provider"
    )

    # Use provided seqera provider or create a new one
    if seqera_provider is not None:
        provider = seqera_provider
        pulumi.log.info("Using existing Seqera provider")
    else:
        # Import here to avoid circular imports
        from ..providers.seqera import create_seqera_provider

        try:
            provider = create_seqera_provider(config)
        except Exception as e:
            pulumi.log.error(f"Failed to create Seqera provider: {e}")
            raise

    # Load all configuration files
    try:
        cpu_config = load_config_file(CONFIG_FILES["cpu"])
        gpu_config = load_config_file(CONFIG_FILES["gpu"])
        arm_config = load_config_file(CONFIG_FILES["arm"])
    except ConfigurationError as e:
        pulumi.log.error(f"Configuration loading failed: {e}")
        raise

    # Validate workspace ID
    try:
        workspace_id = float(config["tower_workspace_id"])
        pulumi.log.info(f"Using workspace ID: {workspace_id}")
    except (ValueError, KeyError) as e:
        error_msg = ERROR_MESSAGES["invalid_workspace_id"].format(e)
        raise ValueError(error_msg) from e

    # Create all three compute environments
    environments = {}

    for env_type, config_data in [
        ("cpu", cpu_config),
        ("gpu", gpu_config),
        ("arm", arm_config),
    ]:
        env_name = COMPUTE_ENV_NAMES[env_type]
        description = COMPUTE_ENV_DESCRIPTIONS[env_type]

        environments[f"{env_type}_env"] = create_compute_environment(
            provider=provider,
            name=env_name,
            credentials_id=towerforge_credentials_id,
            workspace_id=workspace_id,
            config_args=config_data,
            description=description,
        )

    return {
        **environments,
        "provider": provider,
    }


def get_compute_environment_ids_terraform(
    terraform_resources: Dict[str, Any],
) -> Dict[str, Any]:
    """Extract compute environment IDs from Terraform provider resources.

    Args:
        terraform_resources: Dictionary containing terraform resources

    Returns:
        Dict[str, Any]: Dictionary mapping environment types to their IDs
    """
    return {
        "cpu": terraform_resources["cpu_env"].compute_env_id,
        "gpu": terraform_resources["gpu_env"].compute_env_id,
        "arm": terraform_resources["arm_env"].compute_env_id,
    }
