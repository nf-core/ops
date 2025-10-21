"""Seqera Platform compute environment deployment using Seqera Terraform provider."""

import json
import os
from typing import Dict, Any, Optional

import pulumi
import pulumi_seqera as seqera

from utils.constants import (
    COMPUTE_ENV_NAMES,
    COMPUTE_ENV_DESCRIPTIONS,
    CONFIG_FILES,
    NEXTFLOW_CONFIG_FILES,
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


def load_nextflow_config(env_type: str) -> str:
    """Load and merge Nextflow configuration from base and environment-specific files.

    Args:
        env_type: Environment type (cpu, gpu, arm)

    Returns:
        str: Merged Nextflow configuration content

    Raises:
        ConfigurationError: If file loading fails
    """
    config_file = NEXTFLOW_CONFIG_FILES.get(env_type)
    if not config_file:
        raise ConfigurationError(
            f"No Nextflow config file defined for environment type: {env_type}"
        )

    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Nextflow config file not found: {config_file}")

    # Load base configuration
    base_config_file = os.path.join(
        os.path.dirname(config_file), "nextflow-base.config"
    )
    base_config = ""
    if os.path.exists(base_config_file):
        try:
            with open(base_config_file, "r") as f:
                base_config = f.read().strip()
        except Exception as e:
            raise ConfigurationError(
                f"Failed to read base Nextflow config file {base_config_file}: {e}"
            )

    # Load environment-specific configuration
    try:
        with open(config_file, "r") as f:
            env_config = f.read().strip()
    except Exception as e:
        raise ConfigurationError(
            f"Failed to read Nextflow config file {config_file}: {e}"
        )

    # Remove includeConfig line from environment config since we're injecting base config
    env_config_lines = env_config.split("\n")
    env_config_filtered = [
        line
        for line in env_config_lines
        if not line.strip().startswith("includeConfig")
    ]
    env_config_clean = "\n".join(env_config_filtered)

    # Merge base config with environment-specific config
    if base_config:
        merged_config = f"{base_config}\n\n{env_config_clean}"
    else:
        merged_config = env_config_clean

    return merged_config.strip()


def load_config_file(filename: str) -> Dict[str, Any]:
    """Load configuration file with comprehensive error handling.

    Args:
        filename: Path to the JSON configuration file

    Returns:
        Dict[str, Any]: Loaded configuration data

    Raises:
        ConfigurationError: If file loading or parsing fails
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(
            ERROR_MESSAGES["config_file_not_found"].format(filename)
        )

    with open(filename, "r") as f:
        config_data = json.load(f)

    return config_data


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
    env_type: str,
    description: Optional[str] = None,
    depends_on: Optional[list] = None,
    iam_policy_version: Optional[str] = None,
) -> seqera.ComputeEnv:
    """Create a Seqera compute environment using Terraform provider with error handling.

    Args:
        provider: Configured Seqera provider instance
        name: Name for the compute environment
        credentials_id: Seqera credentials ID
        workspace_id: Seqera workspace ID
        config_args: Configuration arguments from JSON file
        env_type: Environment type (cpu, gpu, arm) for loading external nextflow config
        description: Optional description for the compute environment
        depends_on: Optional list of resources this compute environment depends on
        iam_policy_version: Optional IAM policy version hash to trigger recreation on policy changes

    Returns:
        seqera.ComputeEnv: Created compute environment resource

    Raises:
        ComputeEnvironmentError: If compute environment creation fails
        ValueError: If required parameters are missing
        ConfigurationError: If nextflow config loading fails
    """
    pulumi.log.info(f"Creating compute environment: {name}")

    # Validate input parameters
    if not name or not credentials_id:
        raise ValueError(ERROR_MESSAGES["missing_compute_env_params"].format(name))

    if not config_args:
        raise ValueError(ERROR_MESSAGES["missing_config_args"].format(name))

    # Create the forge configuration
    forge_config = create_forge_config(config_args)

    # Load Nextflow configuration from external file
    nextflow_config = load_nextflow_config(env_type)

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
        nextflow_config=nextflow_config,  # Use external config file
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

    # Add IAM policy version to compute environment description to trigger recreation on policy changes
    if iam_policy_version:
        # Append policy version hash to description to force recreation when IAM policies change
        policy_suffix = f" (IAM Policy Version: {iam_policy_version[:8]})"
        if description:
            compute_env_args = seqera.ComputeEnvComputeEnvArgs(
                name=name,
                platform="aws-batch",
                credentials_id=credentials_id,
                config=compute_env_config,
                description=f"{description}{policy_suffix}",
            )
        else:
            compute_env_args = seqera.ComputeEnvComputeEnvArgs(
                name=name,
                platform="aws-batch",
                credentials_id=credentials_id,
                config=compute_env_config,
                description=f"Compute environment{policy_suffix}",
            )

    # Create the compute environment resource
    resource_options = pulumi.ResourceOptions(
        provider=provider,
        # Force delete before replace to avoid name conflicts
        delete_before_replace=True,
        # Add custom timeout for compute environment creation
        custom_timeouts=pulumi.CustomTimeouts(
            create=TIMEOUTS["compute_env_create"],
            update=TIMEOUTS["compute_env_update"],
            delete=TIMEOUTS["compute_env_delete"],
        ),
    )

    # Add dependencies if specified
    if depends_on:
        resource_options.depends_on = depends_on

    compute_env = seqera.ComputeEnv(
        name,
        compute_env=compute_env_args,
        workspace_id=workspace_id,
        opts=resource_options,
    )

    return compute_env


def deploy_seqera_environments_terraform(
    config: Dict[str, Any],
    towerforge_credentials_id: str,
    seqera_provider: Optional[seqera.Provider] = None,
    seqera_credential_resource: Optional[seqera.Credential] = None,
    iam_policy_hash: Optional[str] = None,
) -> Dict[str, Any]:
    """Deploy Seqera Platform compute environments using Terraform provider.

    Args:
        config: Configuration dictionary
        towerforge_credentials_id: Dynamic TowerForge credentials ID
        seqera_provider: Optional existing Seqera provider instance
        seqera_credential_resource: Optional Seqera credential resource for dependency
        iam_policy_hash: Optional IAM policy hash to force recreation on policy changes

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
        from providers.seqera import create_seqera_provider

        provider = create_seqera_provider(config)

    # Load all configuration files
    cpu_config = load_config_file(CONFIG_FILES["cpu"])
    gpu_config = load_config_file(CONFIG_FILES["gpu"])
    arm_config = load_config_file(CONFIG_FILES["arm"])

    # Validate workspace ID
    workspace_id = float(config["tower_workspace_id"])

    # Create all three compute environments
    environments = {}

    # Set up dependencies - compute environments depend on Seqera credential resource
    depends_on_resources = []
    if seqera_credential_resource:
        depends_on_resources.append(seqera_credential_resource)

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
            env_type=env_type,
            description=description,
            depends_on=depends_on_resources if depends_on_resources else None,
            iam_policy_version=iam_policy_hash,
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
