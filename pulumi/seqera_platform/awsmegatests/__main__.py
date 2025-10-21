"""Pulumi program for Seqera Platform - AWS Megatests workspace"""

import sys
from pathlib import Path

# Add shared module to Python path
shared_path = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(shared_path))

import pulumi

# Import shared modules
from providers import (
    create_aws_provider,
    create_github_provider,
    create_seqera_provider,
)
from config import get_configuration
from infrastructure import create_s3_infrastructure, create_towerforge_credentials
from infrastructure import (
    deploy_seqera_environments_terraform,
    get_compute_environment_ids_terraform,
)
from integrations import create_github_resources, create_github_credential
from integrations.workspace_participants_command import (
    create_individual_member_commands,
)

# Import workspace-specific configuration
from workspace_config import get_workspace_config


def main():
    """Main Pulumi program function for AWS Megatests workspace"""

    # Get workspace-specific configuration
    workspace_config = get_workspace_config()

    # Get ESC configuration
    config = get_configuration()

    # Create providers
    aws_provider = create_aws_provider()
    github_provider = create_github_provider(config["github_token"])
    seqera_provider = create_seqera_provider(config)

    # Create GitHub credential in Seqera Platform
    github_credential, github_credential_id = create_github_credential(
        seqera_provider=seqera_provider,
        workspace_id=int(config["tower_workspace_id"]),
        github_token=config.get("platform_github_org_token", ""),
    )

    # Set up S3 infrastructure
    s3_resources = create_s3_infrastructure(aws_provider)
    nf_core_awsmegatests_bucket = s3_resources["bucket"]

    # Create TowerForge IAM credentials and upload to Seqera Platform
    (
        towerforge_access_key_id,
        towerforge_access_key_secret,
        seqera_credentials_id,
        seqera_credential_resource,
        iam_policy_hash,
    ) = create_towerforge_credentials(
        aws_provider,
        nf_core_awsmegatests_bucket,
        seqera_provider,
        float(config["tower_workspace_id"]),
    )

    # Deploy Seqera Platform compute environments
    terraform_resources = deploy_seqera_environments_terraform(
        config,
        seqera_credentials_id,
        seqera_provider,
        seqera_credential_resource,
        iam_policy_hash,
    )

    # Get compute environment IDs
    compute_env_ids = get_compute_environment_ids_terraform(terraform_resources)
    deployment_method = "terraform-provider"

    # Create GitHub resources
    github_resources = create_github_resources(
        github_provider,
        compute_env_ids,
        config["tower_workspace_id"],
        tower_access_token=config["tower_access_token"],
    )

    # Add workspace participants
    setup_cmd, member_commands = create_individual_member_commands(
        workspace_id=int(config["tower_workspace_id"]),
        token=config["tower_access_token"],
        github_token=config["github_token"],
        opts=pulumi.ResourceOptions(depends_on=[seqera_credential_resource]),
    )

    # Exports
    pulumi.export(
        "workspace",
        {
            "name": workspace_config["workspace_name"],
            "organization": workspace_config["organization_name"],
            "workspace_id": config["tower_workspace_id"],
        },
    )

    pulumi.export(
        "megatests_bucket",
        {
            "name": nf_core_awsmegatests_bucket.bucket,
            "arn": nf_core_awsmegatests_bucket.arn,
            "region": workspace_config["aws_region"],
        },
    )

    pulumi.export(
        "github_resources",
        {
            "variables": {
                k: v.id for k, v in github_resources.get("variables", {}).items()
            }
            if github_resources.get("variables")
            else {},
            "secrets": {k: v.id for k, v in github_resources.get("secrets", {}).items()}
            if github_resources.get("secrets")
            else {},
            "manual_secret_commands": github_resources.get("gh_cli_commands", []),
        },
    )

    pulumi.export("compute_env_ids", compute_env_ids)
    pulumi.export("deployment_method", deployment_method)

    pulumi.export(
        "github_credential",
        {
            "credential_id": github_credential_id,
            "credential_name": "nf-core-github-finegrained",
        },
    )

    pulumi.export(
        "terraform_resources",
        {
            "cpu_env_id": terraform_resources["cpu_env"].compute_env_id,
            "gpu_env_id": terraform_resources["gpu_env"].compute_env_id,
            "arm_env_id": terraform_resources["arm_env"].compute_env_id,
        },
    )

    pulumi.export(
        "workspace_participants",
        {
            "setup_command_id": setup_cmd.id,
            "individual_member_commands": {
                username: {"command_id": cmd.id, "github_username": username}
                for username, cmd in member_commands.items()
            },
            "total_tracked_members": len(member_commands),
        },
    )


if __name__ == "__main__":
    main()
