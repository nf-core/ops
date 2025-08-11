"""An AWS Python Pulumi program for nf-core megatests infrastructure"""

import pulumi
import pulumi_aws as aws

# Import our modular components
from providers import create_aws_provider, create_github_provider
from secrets_manager import get_configuration
from s3_infrastructure import create_s3_infrastructure
from towerforge_credentials import create_towerforge_credentials

# seqera_deployment deprecated - using Terraform provider only
from seqera_terraform import (
    deploy_seqera_environments_terraform,
    get_compute_environment_ids_terraform,
)
from github_integration import create_github_resources


def main():
    """Main Pulumi program function"""

    # Step 1: Get configuration from ESC environment and config
    config = get_configuration()

    # Step 2: Create AWS and GitHub providers
    # AWS provider uses ESC-provided credentials automatically
    aws_provider = create_aws_provider()
    github_provider = create_github_provider(config["github_token"])

    # Step 4: Set up S3 infrastructure
    s3_resources = create_s3_infrastructure(aws_provider)
    nf_core_awsmegatests_bucket = s3_resources["bucket"]
    # Note: lifecycle_configuration is managed manually, not used in exports

    # Step 5: Create TowerForge IAM credentials
    towerforge_access_key_id, towerforge_access_key_secret = (
        create_towerforge_credentials(aws_provider, nf_core_awsmegatests_bucket)
    )

    # Step 6: Deploy Seqera Platform compute environments using Terraform provider
    try:
        pulumi.log.info(
            "Deploying Seqera compute environments using Terraform provider"
        )

        # Deploy using Seqera Terraform provider
        terraform_resources = deploy_seqera_environments_terraform(
            config,
            "tower-awstest",  # AWS credentials name in Seqera Platform
        )

        # Get compute environment IDs from Terraform provider
        compute_env_ids = get_compute_environment_ids_terraform(terraform_resources)
        deployment_method = "terraform-provider"

        pulumi.log.info(
            "Successfully deployed compute environments using Seqera Terraform provider"
        )
    except Exception as e:
        error_msg = (
            f"Seqera deployment failed: {e}. "
            "Common solutions: "
            "1. Verify TOWER_ACCESS_TOKEN has WORKSPACE_ADMIN permissions "
            "2. Check workspace ID is correct in ESC environment "
            "3. Ensure 'tower-awstest' credentials exist in Seqera Platform "
            "4. Verify network connectivity to api.cloud.seqera.io"
        )
        pulumi.log.error(error_msg)
        raise RuntimeError(error_msg)

    # Step 8: Create GitHub resources
    # Full GitHub integration enabled - creates both variables and secrets
    try:
        pulumi.log.info("Creating GitHub organization variables and secrets")

        github_resources = create_github_resources(
            github_provider,
            compute_env_ids,
            config["tower_workspace_id"],
            tower_access_token=config["tower_access_token"],
        )

        pulumi.log.info(
            "Successfully created GitHub variables. Manual secret commands available in outputs."
        )
    except Exception as e:
        error_msg = (
            f"GitHub integration failed: {e}. "
            "This is often harmless if variables already exist (409 errors). "
            "Common issues: "
            "1. GitHub token lacks org-level permissions "
            "2. Variables already exist (409 Already Exists - harmless) "
            "3. Network connectivity to api.github.com"
        )
        pulumi.log.warn(error_msg)
        github_resources = {
            "variables": {},
            "secrets": {},
            "gh_cli_commands": [],
            "note": f"GitHub integration failed: {e}",
        }

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


# Proper Pulumi program entry point
if __name__ == "__main__":
    main()
