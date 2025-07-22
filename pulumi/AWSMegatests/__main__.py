"""An AWS Python Pulumi program"""

import pulumi
import pulumi_github as github
import pulumi_command as command
import pulumi_onepassword as onepassword
from pulumi_aws import s3

# Create an AWS resource (S3 Bucket)
bucket = s3.Bucket("my-bucket")

# Export the name of the bucket
pulumi.export("bucket_name", bucket.id)  # type: ignore[attr-defined]

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

# Get workspace ID from Tower CLI
workspace_cmd = command.local.Command(
    "get-workspace-id",
    create="tw -o nf-core workspaces list --format json | jq -r '.[] | select(.name==\"AWSmegatests\") | .id'",
    environment={
        "TOWER_ACCESS_TOKEN": tower_access_token,
        "ORGANIZATION_NAME": "nf-core",
    },
    opts=pulumi.ResourceOptions(additional_secret_outputs=["stdout"]),
)
workspace_id = workspace_cmd.stdout


# Get compute environment IDs using Tower CLI
def get_compute_env_id(env_name: str, display_name: str) -> str:
    """Get compute environment ID by name"""
    get_env_cmd = command.local.Command(
        f"get-compute-env-{env_name}",
        create=f"tw -o nf-core -w AWSmegatests compute-envs list --format json | jq -r '.[] | select(.name==\"{display_name}\") | .id'",
        environment={
            "TOWER_ACCESS_TOKEN": tower_access_token,
            "ORGANIZATION_NAME": "nf-core",
            "WORKSPACE_NAME": "AWSmegatests",
        },
        opts=pulumi.ResourceOptions(additional_secret_outputs=["stdout"]),
    )
    return get_env_cmd.stdout


# Get compute environment IDs for each environment
cpu_compute_env_id = get_compute_env_id("cpu", "aws_ireland_fusionv2_nvme_cpu")
gpu_compute_env_id = get_compute_env_id(
    "gpu", "aws_ireland_fusionv2_nvme_gpu_snapshots"
)
arm_compute_env_id = get_compute_env_id(
    "arm", "aws_ireland_fusionv2_nvme_cpu_ARM_snapshots"
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
