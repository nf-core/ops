"""Pulumi program for Seqera Platform - Resource Optimization workspace"""

import sys
from pathlib import Path

# Add shared module to Python path
shared_path = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(shared_path))

# Add sdks directory to Python path for pulumi_seqera
sdks_path = Path(__file__).parent / "sdks" / "seqera"
sys.path.insert(0, str(sdks_path))

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
    """Main Pulumi program function for Resource Optimization workspace"""

    # Get workspace-specific configuration
    workspace_config = get_workspace_config()

    # Get ESC configuration
    config = get_configuration()

    # Create providers
    aws_provider = create_aws_provider()
    seqera_provider = create_seqera_provider(config)

    # Only create GitHub provider if GitHub integration is enabled
    github_provider = None
    github_credential = None
    github_credential_id = None
    if workspace_config["github_integration"]["enabled"]:
        github_provider = create_github_provider(config["github_token"])
        # Create GitHub credential in Seqera Platform
        github_credential, github_credential_id = create_github_credential(
            seqera_provider=seqera_provider,
            workspace_id=int(config["tower_workspace_id"]),
            github_token=config.get("platform_github_org_token", ""),
        )

    # Set up S3 infrastructure with workspace-specific bucket name
    # Create new bucket (don't import existing) for this workspace
    s3_resources = create_s3_infrastructure(
        aws_provider,
        bucket_name=workspace_config["s3_bucket_name"],
        import_existing=False
    )
    resource_opt_bucket = s3_resources["bucket"]

    # Create TowerForge IAM credentials and upload to Seqera Platform
    # Use workspace name to create unique IAM resource names
    (
        towerforge_access_key_id,
        towerforge_access_key_secret,
        seqera_credentials_id,
        seqera_credential_resource,
        iam_policy_hash,
    ) = create_towerforge_credentials(
        aws_provider,
        resource_opt_bucket,
        seqera_provider,
        float(config["tower_workspace_id"]),
        workspace_name=workspace_config["workspace_name"],
    )

    # Deploy Seqera Platform compute environments (CPU only for this workspace)
    # workspace_config controls which environments are deployed
    terraform_resources = deploy_seqera_environments_terraform(
        config,
        seqera_credentials_id,
        seqera_provider,
        seqera_credential_resource,
        iam_policy_hash,
        workspace_config=workspace_config,
    )

    # Get compute environment IDs
    compute_env_ids = get_compute_environment_ids_terraform(terraform_resources)
    deployment_method = "terraform-provider"

    # Create GitHub resources only if enabled
    github_resources = {}
    if workspace_config["github_integration"]["enabled"] and github_provider:
        github_resources = create_github_resources(
            github_provider,
            compute_env_ids,
            config["tower_workspace_id"],
            tower_access_token=config["tower_access_token"],
        )

    # Add workspace participants if enabled
    if workspace_config["workspace_participants"]["enabled"]:
        setup_cmd, member_commands = create_individual_member_commands(
            workspace_id=int(config["tower_workspace_id"]),
            token=config["tower_access_token"],
            github_token=config["github_token"],
            opts=pulumi.ResourceOptions(depends_on=[seqera_credential_resource]),
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

    # Exports
    pulumi.export(
        "workspace",
        {
            "name": workspace_config["workspace_name"],
            "organization": workspace_config["organization_name"],
            "workspace_id": config["tower_workspace_id"],
            "description": workspace_config["description"],
        },
    )

    pulumi.export(
        "s3_bucket",
        {
            "name": resource_opt_bucket.bucket,
            "arn": resource_opt_bucket.arn,
            "region": workspace_config["aws_region"],
        },
    )

    if github_resources:
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
            },
        )

    pulumi.export("compute_env_ids", compute_env_ids)
    pulumi.export("deployment_method", deployment_method)

    if github_credential_id:
        pulumi.export(
            "github_credential",
            {
                "credential_id": github_credential_id,
                "credential_name": "nf-core-github-finegrained",
            },
        )

    # Only export enabled compute environments
    terraform_exports = {}
    if workspace_config["compute_environments"]["cpu"]["enabled"]:
        terraform_exports["cpu_env_id"] = terraform_resources["cpu_env"].compute_env_id

    pulumi.export("terraform_resources", terraform_exports)


if __name__ == "__main__":
    main()
