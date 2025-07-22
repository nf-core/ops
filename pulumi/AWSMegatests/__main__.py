"""An AWS Python Pulumi program"""

import pulumi
import pulumi_github as github
import pulumi_command as command
import pulumi_onepassword as onepassword
from pulumi_aws import s3

# Import existing AWS resources used by nf-core megatests
# S3 bucket for Nextflow work directory (already exists)
nf_core_awsmegatests_bucket = s3.Bucket(
    "nf-core-awsmegatests",
    bucket="nf-core-awsmegatests",
    opts=pulumi.ResourceOptions(
        import_="nf-core-awsmegatests",  # Import existing bucket
        protect=True,  # Protect from accidental deletion
    ),
)

# Export the bucket information
pulumi.export(
    "megatests_bucket",
    {
        "name": nf_core_awsmegatests_bucket.bucket,
        "arn": nf_core_awsmegatests_bucket.arn,
        "region": "eu-west-1",
    },
)

# Configure the 1Password provider explicitly
onepassword_config = pulumi.Config("pulumi-onepassword")
onepassword_provider = onepassword.Provider(
    "onepassword-provider",
    service_account_token=onepassword_config.require_secret("service_account_token"),
)

# Get secrets from 1Password using the provider
tower_access_token_item = onepassword.get_item_output(
    vault="Employee",
    title="Seqera Platform Token",
    opts=pulumi.InvokeOptions(provider=onepassword_provider),
)
tower_access_token = tower_access_token_item.credential

github_token_item = onepassword.get_item_output(
    vault="Employee",
    title="Github Token nf-core",
    opts=pulumi.InvokeOptions(provider=onepassword_provider),
)
github_token = github_token_item.credential

# Deploy seqerakit environments and extract compute IDs
# NOTE: We could check for tw-cli availability here, but we'll let seqerakit
# throw the appropriate error if it's missing. Seqerakit requires tw-cli to be
# installed and available in PATH.
#
# NOTE: Seqerakit will create and manage:
# - AWS Batch compute environments and job queues
# - IAM roles (ExecutionRole, FargateRole) with TowerForge prefix
# - Security groups and networking resources
# These are managed by Seqera Platform and should not be imported into Pulumi
seqerakit_environment = {
    "TOWER_ACCESS_TOKEN": tower_access_token,
    "ORGANIZATION_NAME": "nf-core",
    "WORKSPACE_NAME": "AWSmegatests",
    "AWS_CREDENTIALS_NAME": "tower-awstest",
    "AWS_REGION": "eu-west-1",
    "AWS_WORK_DIR": "s3://nf-core-awsmegatests",
    "AWS_COMPUTE_ENV_ALLOWED_BUCKETS": "s3://ngi-igenomes,s3://annotation-cache",
}

# Deploy CPU environment with seqerakit
cpu_deploy_cmd = command.local.Command(
    "deploy-cpu-environment",
    create="cd seqerakit && seqerakit aws_ireland_fusionv2_nvme_cpu_current.yml",
    environment=seqerakit_environment,
    opts=pulumi.ResourceOptions(additional_secret_outputs=["stdout"]),
)

# Deploy GPU environment with seqerakit
gpu_deploy_cmd = command.local.Command(
    "deploy-gpu-environment",
    create="cd seqerakit && seqerakit aws_ireland_fusionv2_nvme_gpu_current.yml",
    environment=seqerakit_environment,
    opts=pulumi.ResourceOptions(
        additional_secret_outputs=["stdout"], depends_on=[cpu_deploy_cmd]
    ),
)

# Deploy ARM environment with seqerakit
arm_deploy_cmd = command.local.Command(
    "deploy-arm-environment",
    create="cd seqerakit && seqerakit aws_ireland_fusionv2_nvme_cpu_arm_current.yml",
    environment=seqerakit_environment,
    opts=pulumi.ResourceOptions(
        additional_secret_outputs=["stdout"], depends_on=[gpu_deploy_cmd]
    ),
)

# Get workspace ID from Tower CLI
workspace_cmd = command.local.Command(
    "get-workspace-id",
    create="tw -o nf-core workspaces list --format json | jq -r '.[] | select(.name==\"AWSmegatests\") | .id'",
    environment=seqerakit_environment,
    opts=pulumi.ResourceOptions(
        additional_secret_outputs=["stdout"], depends_on=[arm_deploy_cmd]
    ),
)
workspace_id = workspace_cmd.stdout


# Extract compute environment IDs after deployment
def get_compute_env_id(env_name: str, display_name: str, depends_on_cmd) -> str:
    """Get compute environment ID by name after deployment"""
    get_env_cmd = command.local.Command(
        f"get-compute-env-{env_name}",
        create=f"tw -o nf-core -w AWSmegatests compute-envs list --format json | jq -r '.[] | select(.name==\"{display_name}\") | .id'",
        environment=seqerakit_environment,
        opts=pulumi.ResourceOptions(
            additional_secret_outputs=["stdout"], depends_on=[depends_on_cmd]
        ),
    )
    return get_env_cmd.stdout


# Get compute environment IDs for each environment after deployment
cpu_compute_env_id = get_compute_env_id(
    "cpu", "aws_ireland_fusionv2_nvme_cpu", cpu_deploy_cmd
)
gpu_compute_env_id = get_compute_env_id(
    "gpu", "aws_ireland_fusionv2_nvme_gpu_snapshots", gpu_deploy_cmd
)
arm_compute_env_id = get_compute_env_id(
    "arm", "aws_ireland_fusionv2_nvme_cpu_ARM_snapshots", arm_deploy_cmd
)

# Create GitHub provider
github_provider = github.Provider("github", token=github_token)

# Create org-level GitHub secrets for compute environment IDs
cpu_secret = github.ActionsOrganizationSecret(
    "tower-compute-env-cpu",
    visibility="private",
    secret_name="TOWER_COMPUTE_ENV_CPU",
    plaintext_value=cpu_compute_env_id,
    opts=pulumi.ResourceOptions(provider=github_provider),
)

gpu_secret = github.ActionsOrganizationSecret(
    "tower-compute-env-gpu",
    visibility="private",
    secret_name="TOWER_COMPUTE_ENV_GPU",
    plaintext_value=gpu_compute_env_id,
    opts=pulumi.ResourceOptions(provider=github_provider),
)

arm_secret = github.ActionsOrganizationSecret(
    "tower-compute-env-arm",
    visibility="private",
    secret_name="TOWER_COMPUTE_ENV_ARM",
    plaintext_value=arm_compute_env_id,
    opts=pulumi.ResourceOptions(provider=github_provider),
)

# Create org-level GitHub secret for Seqera Platform API token
seqera_token_secret = github.ActionsOrganizationSecret(
    "tower-access-token",
    visibility="private",
    secret_name="TOWER_ACCESS_TOKEN",
    plaintext_value=tower_access_token,
    opts=pulumi.ResourceOptions(provider=github_provider),
)

# Create org-level GitHub secret for workspace ID
workspace_id_secret = github.ActionsOrganizationSecret(
    "tower-workspace-id",
    visibility="private",
    secret_name="TOWER_WORKSPACE_ID",
    plaintext_value=workspace_id,
    opts=pulumi.ResourceOptions(provider=github_provider),
)

# Export the created secrets
pulumi.export(
    "github_secrets",
    {
        "compute_env_cpu": cpu_secret.secret_name,
        "compute_env_gpu": gpu_secret.secret_name,
        "compute_env_arm": arm_secret.secret_name,
        "tower_access_token": seqera_token_secret.secret_name,
        "tower_workspace_id": workspace_id_secret.secret_name,
    },
)

# Export compute environment IDs for reference
pulumi.export(
    "compute_env_ids",
    {"cpu": cpu_compute_env_id, "gpu": gpu_compute_env_id, "arm": arm_compute_env_id},
)

# Export workspace ID for reference
pulumi.export("workspace_id", workspace_id)

# Export deployment status for reference
pulumi.export(
    "seqerakit_deployments",
    {
        "cpu_deployment": cpu_deploy_cmd.stdout,
        "gpu_deployment": gpu_deploy_cmd.stdout,
        "arm_deployment": arm_deploy_cmd.stdout,
    },
)
