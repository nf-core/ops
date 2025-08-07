"""An AWS Python Pulumi program for nf-core megatests infrastructure"""

import pulumi
import pulumi_aws as aws

# Import our modular components
from providers import create_providers, create_aws_provider, create_github_provider
from secrets_manager import get_secrets
from s3_infrastructure import create_s3_infrastructure
from towerforge_credentials import create_towerforge_credentials
from seqera_deployment import deploy_seqera_environments, query_compute_environment_ids

# Step 1: Initialize 1Password provider
providers = create_providers()
onepassword_provider = providers["onepassword"]

# Step 2: Get secrets from 1Password
op_secrets = get_secrets(onepassword_provider)

# Step 3: Create AWS and GitHub providers with secrets from 1Password
aws_provider = create_aws_provider(
    op_secrets["aws_access_key_id"], op_secrets["aws_secret_access_key"]
)
github_provider = create_github_provider(op_secrets["github_token"])

# Step 4: Set up S3 infrastructure
s3_resources = create_s3_infrastructure(aws_provider)
nf_core_awsmegatests_bucket = s3_resources["bucket"]
bucket_lifecycle_configuration = s3_resources["lifecycle_configuration"]

# Step 5: Create TowerForge IAM credentials
towerforge_access_key_id, towerforge_access_key_secret = create_towerforge_credentials(
    aws_provider, nf_core_awsmegatests_bucket
)

# Step 6: Deploy Seqera Platform compute environments
seqera_resources = deploy_seqera_environments(
    op_secrets, towerforge_access_key_id, towerforge_access_key_secret
)
cpu_deploy_cmd = seqera_resources["cpu_deploy_cmd"]
gpu_deploy_cmd = seqera_resources["gpu_deploy_cmd"]
arm_deploy_cmd = seqera_resources["arm_deploy_cmd"]

# Step 7: Query compute environment IDs
compute_env_ids = query_compute_environment_ids(op_secrets["tower_access_token"])

# Step 8: Create GitHub resources
# Temporarily commented out due to GitHub token permissions issue
# github_resources = create_github_resources(
#     github_provider, compute_env_ids, op_secrets["tower_workspace_id"]
# )
github_resources: dict = {"variables": {}, "secrets": {}}

# Exports
pulumi.export(
    "megatests_bucket",
    {
        "name": nf_core_awsmegatests_bucket.bucket,
        "arn": nf_core_awsmegatests_bucket.arn,
        "region": "eu-west-1",
        "lifecycle_configuration": bucket_lifecycle_configuration.id,
    },
)

pulumi.export(
    "github_resources",
    {
        "note": "GitHub resources temporarily disabled due to permissions issue",
        "variables": {},
        "secrets": {},
    },
)

pulumi.export("compute_env_ids", compute_env_ids)
pulumi.export("workspace_id", op_secrets["tower_workspace_id"])

pulumi.export(
    "seqerakit_deployments",
    {
        "cpu_deployment": cpu_deploy_cmd.stdout,
        "gpu_deployment": gpu_deploy_cmd.stdout,
        "arm_deployment": arm_deploy_cmd.stdout,
    },
)

towerforge_resources = {
    "user": {
        "name": "TowerForge-AWSMegatests",
        "arn": f"arn:aws:iam::{aws.get_caller_identity().account_id}:user/TowerForge-AWSMegatests",
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
