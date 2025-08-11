"""An AWS Python Pulumi program for nf-core megatests infrastructure"""

import pulumi
import pulumi_aws as aws

# Import our modular components
from providers import create_aws_provider, create_github_provider
from secrets_manager import get_configuration
from s3_infrastructure import create_s3_infrastructure
from towerforge_credentials import create_towerforge_credentials
from seqera_deployment import deploy_seqera_environments, query_compute_environment_ids
from seqera_terraform import deploy_seqera_environments_terraform, get_compute_environment_ids_terraform
from github_integration import create_github_resources

# Step 1: Get configuration from ESC environment and config
config = get_configuration()

# Step 2: Create AWS and GitHub providers
# AWS provider uses ESC-provided credentials automatically
aws_provider = create_aws_provider()
github_provider = create_github_provider(config["github_token"])

# Step 4: Set up S3 infrastructure
s3_resources = create_s3_infrastructure(aws_provider)
nf_core_awsmegatests_bucket = s3_resources["bucket"]
bucket_lifecycle_configuration = s3_resources["lifecycle_configuration"]

# Step 5: Create TowerForge IAM credentials
towerforge_access_key_id, towerforge_access_key_secret = create_towerforge_credentials(
    aws_provider, nf_core_awsmegatests_bucket
)

# Step 6: Deploy Seqera Platform compute environments using both approaches

# Option A: Original seqerakit approach (maintained for backup/comparison)
seqera_resources = deploy_seqera_environments(
    config, towerforge_access_key_id, towerforge_access_key_secret
)
cpu_deploy_cmd = seqera_resources["cpu_deploy_cmd"]
gpu_deploy_cmd = seqera_resources["gpu_deploy_cmd"]
arm_deploy_cmd = seqera_resources["arm_deploy_cmd"]

# Query compute environment IDs from seqerakit approach
compute_env_ids_seqerakit = query_compute_environment_ids(config["tower_access_token"])

# Option B: New Terraform provider approach (primary deployment method)
try:
    # We need to pass the credentials_id as a string - using the TowerForge credentials name
    terraform_resources = deploy_seqera_environments_terraform(
        config, 
        "tower-awstest"  # This should match the AWS_CREDENTIALS_NAME from seqerakit
    )
    
    # Get compute environment IDs from Terraform provider
    compute_env_ids_terraform = get_compute_environment_ids_terraform(terraform_resources)
    
    # Use Terraform provider IDs as primary
    compute_env_ids = compute_env_ids_terraform
    deployment_method = "terraform-provider"
    
    pulumi.log.info("Successfully deployed compute environments using Seqera Terraform provider")
    
except Exception as e:
    # Fallback to seqerakit approach if Terraform provider fails
    pulumi.log.warn(f"Terraform provider deployment failed, falling back to seqerakit: {e}")
    compute_env_ids = compute_env_ids_seqerakit
    deployment_method = "seqerakit-fallback"

# Step 8: Create GitHub resources
# Full GitHub integration enabled - creates both variables and secrets
try:
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
    pulumi.log.warn(f"Failed to create GitHub resources: {e}")
    github_resources = {
        "variables": {},
        "secrets": {},
        "gh_cli_commands": [],
        "note": "Failed to create resources",
    }

# Exports
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
        "variables": {k: v.id for k, v in github_resources.get("variables", {}).items()}
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

# Export both deployment approaches for comparison
pulumi.export("compute_env_ids_seqerakit", compute_env_ids_seqerakit)

# Export Terraform provider resources if available
if deployment_method == "terraform-provider":
    pulumi.export(
        "terraform_resources",
        {
            "cpu_env_id": terraform_resources["cpu_env"].compute_env_id,
            "gpu_env_id": terraform_resources["gpu_env"].compute_env_id,
            "arm_env_id": terraform_resources["arm_env"].compute_env_id,
            "deployment_method": "seqera-terraform-provider",
        },
    )

pulumi.export(
    "seqerakit_deployments",
    {
        "cpu_deployment": cpu_deploy_cmd.stdout,
        "gpu_deployment": gpu_deploy_cmd.stdout,
        "arm_deployment": arm_deploy_cmd.stdout,
        "note": "Legacy seqerakit deployment maintained for backup/comparison",
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
