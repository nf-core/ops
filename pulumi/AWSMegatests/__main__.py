"""An AWS Python Pulumi program"""

import os
import pulumi
import pulumi_github as github
import pulumi_command as command
import pulumi_onepassword as onepassword
import pulumi_aws as aws
from pulumi_aws import s3

# Configure the 1Password provider explicitly
onepassword_config = pulumi.Config("pulumi-onepassword")
onepassword_provider = onepassword.Provider(
    "onepassword-provider",
    service_account_token=onepassword_config.require_secret("service_account_token"),
)

# Get secrets from 1Password using the provider
# Get Tower access token from 1Password
tower_access_token_item = onepassword.get_item_output(
    vault="Dev",
    title="Seqera Platform",
    opts=pulumi.InvokeOptions(provider=onepassword_provider),
)
tower_access_token = tower_access_token_item.credential

# For workspace ID, since it's likely a custom field, we'll use environment variable
# The workspace ID should be set in .envrc as TOWER_WORKSPACE_ID from 1Password
tower_workspace_id = os.environ.get("TOWER_WORKSPACE_ID")

github_token_item = onepassword.get_item_output(
    vault="Dev",
    title="GitHub nf-core PA Token Pulumi",
    opts=pulumi.InvokeOptions(provider=onepassword_provider),
)
github_token = github_token_item.credential

# Use default AWS provider which will read from environment variables
# (set via .envrc with 1Password integration)
aws_provider = aws.Provider("aws-provider", region="eu-west-1")

# Configure GitHub provider with 1Password credentials
github_provider = github.Provider(
    "github-provider", token=github_token, owner="nf-core"
)

# Import existing AWS resources used by nf-core megatests
# S3 bucket for Nextflow work directory (already exists)
nf_core_awsmegatests_bucket = s3.Bucket(
    "nf-core-awsmegatests",
    bucket="nf-core-awsmegatests",
    opts=pulumi.ResourceOptions(
        import_="nf-core-awsmegatests",  # Import existing bucket
        protect=True,  # Protect from accidental deletion
        provider=aws_provider,  # Use configured AWS provider
        ignore_changes=[
            "cors_rules",
            "lifecycle_rules",
            "versioning",
        ],  # Don't modify existing configurations
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
    "TOWER_WORKSPACE_ID": tower_workspace_id,  # Get from 1Password
    "ORGANIZATION_NAME": "nf-core",
    "WORKSPACE_NAME": "AWSmegatests",
    "AWS_CREDENTIALS_NAME": "tower-awstest",
    "AWS_REGION": "eu-west-1",
    "AWS_WORK_DIR": "s3://nf-core-awsmegatests",
    "AWS_COMPUTE_ENV_ALLOWED_BUCKETS": "s3://ngi-igenomes,s3://annotation-cache",
    # Add AWS credentials for seqerakit to create compute environments
    "AWS_ACCESS_KEY_ID": pulumi.Config("aws").get("accessKey")
    or os.environ.get("AWS_ACCESS_KEY_ID"),
    "AWS_SECRET_ACCESS_KEY": pulumi.Config("aws").get_secret("secretKey")
    or os.environ.get("AWS_SECRET_ACCESS_KEY"),
    # Tower CLI configuration - use standard Seqera Cloud endpoint
    "TOWER_API_ENDPOINT": "https://api.cloud.seqera.io",
}

# Deploy CPU environment with seqerakit (with JSON output)
# NOTE: Tower access token needs to be valid and have permissions for nf-core/AWSmegatests workspace
cpu_deploy_cmd = command.local.Command(
    "deploy-cpu-environment",
    create="cd seqerakit && uv run seqerakit --json aws_ireland_fusionv2_nvme_cpu_current.yml",
    environment=seqerakit_environment,
    opts=pulumi.ResourceOptions(additional_secret_outputs=["stdout"]),
)

# Deploy GPU environment with seqerakit (with JSON output)
gpu_deploy_cmd = command.local.Command(
    "deploy-gpu-environment",
    create="cd seqerakit && uv run seqerakit --json aws_ireland_fusionv2_nvme_gpu_current.yml",
    environment=seqerakit_environment,
    opts=pulumi.ResourceOptions(
        additional_secret_outputs=["stdout"], depends_on=[cpu_deploy_cmd]
    ),
)

# Deploy ARM environment with seqerakit (with JSON output)
arm_deploy_cmd = command.local.Command(
    "deploy-arm-environment",
    create="cd seqerakit && uv run seqerakit --json aws_ireland_fusionv2_nvme_cpu_arm_current.yml",
    environment=seqerakit_environment,
    opts=pulumi.ResourceOptions(
        additional_secret_outputs=["stdout"], depends_on=[gpu_deploy_cmd]
    ),
)

# Workspace ID is now retrieved from 1Password (tower_workspace_id)


# Extract compute environment IDs from seqerakit JSON output
def extract_compute_env_id_from_seqerakit(env_name: str, deploy_cmd) -> str:
    """Extract compute environment ID from seqerakit JSON output using Pulumi's apply method"""

    def create_extraction_command(seqerakit_output: str) -> str:
        extract_cmd = f"""
        set -e
        
        # Save the output to a temp file for processing
        echo '{seqerakit_output}' > /tmp/seqerakit_output_{env_name}.json
        
        # Extract JSON from mixed text/JSON output (redirect debug to stderr)
        JSON_LINE=$(cat /tmp/seqerakit_output_{env_name}.json | grep -E '^\\{{.*\\}}$' | head -1)
        
        if [ -z "$JSON_LINE" ]; then
            echo "PLACEHOLDER_COMPUTE_ENV_ID_{env_name.upper()}"
            exit 0
        fi
        
        echo "$JSON_LINE" > /tmp/seqerakit_clean_{env_name}.json
        
        # Extract compute environment ID from clean JSON
        COMPUTE_ID=$(cat /tmp/seqerakit_clean_{env_name}.json | jq -r '.id // empty' 2>/dev/null || echo "")
        
        if [ -z "$COMPUTE_ID" ] || [ "$COMPUTE_ID" = "null" ]; then
            # Try alternative field name
            COMPUTE_ID=$(cat /tmp/seqerakit_clean_{env_name}.json | jq -r '.computeEnvId // empty' 2>/dev/null || echo "")
        fi
        
        if [ -z "$COMPUTE_ID" ] || [ "$COMPUTE_ID" = "null" ]; then
            echo "PLACEHOLDER_COMPUTE_ENV_ID_{env_name.upper()}"
            exit 0
        fi
        
        # Output only the compute environment ID (no debug messages)
        echo "$COMPUTE_ID"
        """
        return extract_cmd

    # Use Pulumi's apply to handle the Output properly
    extract_env_cmd = deploy_cmd.stdout.apply(
        lambda output: command.local.Command(
            f"extract-compute-env-id-{env_name}",
            create=create_extraction_command(output),
            opts=pulumi.ResourceOptions(
                additional_secret_outputs=["stdout"], depends_on=[deploy_cmd]
            ),
        ).stdout
    )

    return extract_env_cmd


# Extract compute environment IDs from seqerakit outputs
cpu_compute_env_id = extract_compute_env_id_from_seqerakit("cpu", cpu_deploy_cmd)
gpu_compute_env_id = extract_compute_env_id_from_seqerakit("gpu", gpu_deploy_cmd)
arm_compute_env_id = extract_compute_env_id_from_seqerakit("arm", arm_deploy_cmd)

# GitHub provider already configured above

# Create org-level GitHub variables for compute environment IDs (non-sensitive)
cpu_variable = github.ActionsOrganizationVariable(
    "tower-compute-env-cpu",
    visibility="all",
    variable_name="TOWER_COMPUTE_ENV_CPU",
    value=cpu_compute_env_id,
    opts=pulumi.ResourceOptions(provider=github_provider),
)

gpu_variable = github.ActionsOrganizationVariable(
    "tower-compute-env-gpu",
    visibility="all",
    variable_name="TOWER_COMPUTE_ENV_GPU",
    value=gpu_compute_env_id,
    opts=pulumi.ResourceOptions(provider=github_provider),
)

arm_variable = github.ActionsOrganizationVariable(
    "tower-compute-env-arm",
    visibility="all",
    variable_name="TOWER_COMPUTE_ENV_ARM",
    value=arm_compute_env_id,
    opts=pulumi.ResourceOptions(provider=github_provider),
)

# Create org-level GitHub secret for Seqera Platform API token
seqera_token_secret = github.ActionsOrganizationSecret(
    "tower-access-token",
    visibility="all",
    secret_name="TOWER_ACCESS_TOKEN",
    plaintext_value=tower_access_token,
    opts=pulumi.ResourceOptions(
        provider=github_provider,
        delete_before_replace=True,  # Workaround for pulumi/pulumi-github#250
    ),
)

# Create org-level GitHub variable for workspace ID (non-sensitive)
workspace_id_variable = github.ActionsOrganizationVariable(
    "tower-workspace-id",
    visibility="all",
    variable_name="TOWER_WORKSPACE_ID",
    value=tower_workspace_id,
    opts=pulumi.ResourceOptions(provider=github_provider),
)

# Export the created GitHub resources
pulumi.export(
    "github_resources",
    {
        "variables": {
            "compute_env_cpu": cpu_variable.variable_name,
            "compute_env_gpu": gpu_variable.variable_name,
            "compute_env_arm": arm_variable.variable_name,
            "tower_workspace_id": workspace_id_variable.variable_name,
        },
        "secrets": {
            "tower_access_token": seqera_token_secret.secret_name,
        },
    },
)

# Export compute environment IDs for reference
pulumi.export(
    "compute_env_ids",
    {"cpu": cpu_compute_env_id, "gpu": gpu_compute_env_id, "arm": arm_compute_env_id},
)

# Export workspace ID for reference
pulumi.export("workspace_id", tower_workspace_id)

# Export deployment status for reference
pulumi.export(
    "seqerakit_deployments",
    {
        "cpu_deployment": cpu_deploy_cmd.stdout,
        "gpu_deployment": gpu_deploy_cmd.stdout,
        "arm_deployment": arm_deploy_cmd.stdout,
    },
)
