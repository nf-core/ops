"""An AWS Python Pulumi program for nf-core megatests infrastructure"""

import pulumi
import pulumi_aws as aws

# Import our modular components
from src.providers import (
    create_aws_provider,
    create_github_provider,
    create_seqera_provider,
)
from src.config import get_configuration
from src.infrastructure import create_s3_infrastructure, create_towerforge_credentials
from src.infrastructure import (
    deploy_seqera_environments_terraform,
    get_compute_environment_ids_terraform,
)
from src.integrations import create_github_resources, create_github_credential
from src.integrations.workspace_participants_command import (
    create_individual_member_commands,
)


def main():
    """Main Pulumi program function"""

    # Step 1: Get configuration from ESC environment and config
    config = get_configuration()

    # Step 2: Create AWS, GitHub, and Seqera providers
    # AWS provider uses ESC-provided credentials automatically
    aws_provider = create_aws_provider()
    github_provider = create_github_provider(config["github_token"])

    # Create Seqera provider early for credential upload
    seqera_provider = create_seqera_provider(config)

    # Step 3.5: Create GitHub fine-grained credential in Seqera Platform
    # This allows Platform to pull pipeline repositories without hitting GitHub rate limits
    github_credential, github_credential_id = create_github_credential(
        seqera_provider=seqera_provider,
        workspace_id=int(config["tower_workspace_id"]),
        github_token=config.get("platform_github_org_token", ""),
    )

    # Step 4: Set up S3 infrastructure
    s3_resources = create_s3_infrastructure(aws_provider)
    nf_core_awsmegatests_bucket = s3_resources["bucket"]
    # Note: lifecycle_configuration is managed manually, not used in exports

    # Step 5: Create TowerForge IAM credentials and upload to Seqera Platform
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

    # Step 6: Deploy Seqera Platform compute environments using Terraform provider
    # Deploy using Seqera Terraform provider with dynamic credentials ID
    terraform_resources = deploy_seqera_environments_terraform(
        config,
        seqera_credentials_id,  # Dynamic TowerForge credentials ID from Seqera Platform
        seqera_provider,  # Reuse existing Seqera provider
        seqera_credential_resource,  # Seqera credential resource for dependency
        iam_policy_hash,  # IAM policy hash to force CE recreation on policy changes
    )

    # Get compute environment IDs from Terraform provider
    compute_env_ids = get_compute_environment_ids_terraform(terraform_resources)
    deployment_method = "terraform-provider"

    # Step 8: Create GitHub resources
    # Full GitHub integration enabled - creates both variables and secrets
    github_resources = create_github_resources(
        github_provider,
        compute_env_ids,
        config["tower_workspace_id"],
        tower_access_token=config["tower_access_token"],
    )

    # Step 9: Add nf-core team members as workspace participants with role precedence
    # Core team → OWNER role, Maintainers → MAINTAIN role
    # Individual member tracking provides granular status per team member

    # Create team data setup and individual member tracking commands
    setup_cmd, member_commands = create_individual_member_commands(
        workspace_id=int(config["tower_workspace_id"]),
        token=config["tower_access_token"],
        github_token=config["github_token"],
        opts=pulumi.ResourceOptions(
            depends_on=[seqera_credential_resource]  # Ensure credentials exist first
        ),
    )

    # Option B: Native Pulumi with HTTP calls (more integrated)
    # Uncomment to use this approach instead:
    # maintainer_emails = load_maintainer_emails_static()
    # participants_results = create_workspace_participants_simple(
    #     workspace_id=pulumi.Output.from_input(config["tower_workspace_id"]),
    #     token=pulumi.Output.from_input(config["tower_access_token"]),
    #     maintainer_emails=maintainer_emails
    # )

    # Exports - All within proper Pulumi program context
    pulumi.export(
        "megatests_bucket",
        {
            "name": nf_core_awsmegatests_bucket.bucket,
            "arn": nf_core_awsmegatests_bucket.arn,
            "region": "eu-west-1",
            "lifecycle_configuration": "managed-manually",
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
            "note": github_resources.get("note", ""),
            "workaround_info": {
                "issue_url": "https://github.com/pulumi/pulumi-github/issues/250",
                "workaround": "Variables via Pulumi with delete_before_replace, secrets via manual gh CLI",
                "instructions": "Run the commands in 'manual_secret_commands' to set GitHub secrets",
            },
        },
    )

    pulumi.export("compute_env_ids", compute_env_ids)
    pulumi.export("workspace_id", config["tower_workspace_id"])
    pulumi.export("deployment_method", deployment_method)

    # Export GitHub credential information
    pulumi.export(
        "github_credential",
        {
            "credential_id": github_credential_id,
            "credential_name": "nf-core-github-finegrained",
            "description": "Fine-grained GitHub token to avoid rate limits when Platform pulls pipeline repositories",
            "provider_type": "github",
            "base_url": "https://github.com/nf-core/",
            "workspace_id": config["tower_workspace_id"],
            "purpose": "Prevents GitHub API rate limiting during pipeline repository access",
        },
    )

    # Export Terraform provider resources
    pulumi.export(
        "terraform_resources",
        {
            "cpu_env_id": terraform_resources["cpu_env"].compute_env_id,
            "gpu_env_id": terraform_resources["gpu_env"].compute_env_id,
            "arm_env_id": terraform_resources["arm_env"].compute_env_id,
            "deployment_method": "seqera-terraform-provider",
        },
    )

    towerforge_resources = {
        "user": {
            "name": "TowerForge-AWSMegatests",
            "arn": f"arn:aws:iam::{aws.get_caller_identity(opts=pulumi.InvokeOptions(provider=aws_provider)).account_id}:user/TowerForge-AWSMegatests",
        },
        "access_key_id": towerforge_access_key_id,
        "access_key_secret": towerforge_access_key_secret,
        "policies": {
            "forge_policy_name": "TowerForge-Forge-Policy",
            "launch_policy_name": "TowerForge-Launch-Policy",
            "s3_policy_name": "TowerForge-S3-Policy",
        },
    }
    pulumi.export("towerforge_iam", towerforge_resources)

    # Export workspace participants management information with individual member tracking
    pulumi.export(
        "workspace_participants",
        {
            "setup_command_id": setup_cmd.id,
            "setup_status": setup_cmd.stdout,
            "individual_member_commands": {
                username: {
                    "command_id": cmd.id,
                    "status": cmd.stdout,  # Contains STATUS lines from script
                    "github_username": username,
                }
                for username, cmd in member_commands.items()
            },
            "total_tracked_members": len(member_commands),
            "workspace_id": config["tower_workspace_id"],
            "note": "Automated team data setup with individual member sync commands and privacy protection",
            "privacy": "Email data generated at runtime, never committed to git",
            "todo": "Replace with seqera_workspace_participant resources when available",
        },
    )


# Proper Pulumi program entry point
if __name__ == "__main__":
    main()
