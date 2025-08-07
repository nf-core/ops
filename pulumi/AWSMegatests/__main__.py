"""An AWS Python Pulumi program"""

import json
import pulumi
import pulumi_github as github
import pulumi_command as command
import pulumi_onepassword as onepassword
import pulumi_aws as aws
from pulumi_aws import s3
from towerforge_credentials import create_towerforge_credentials

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


# Access the TOWER_ACCESS_TOKEN field from the item sections
def find_field_value(fields):
    for field in fields:
        if hasattr(field, "label") and field.label == "TOWER_ACCESS_TOKEN":
            return field.value
        # Fallback to check if field has different attribute names
        if hasattr(field, "id") and field.id == "TOWER_ACCESS_TOKEN":
            return field.value
    return None


tower_access_token = tower_access_token_item.sections[0].fields.apply(find_field_value)

# Get workspace ID from 1Password (using static value for now)
# TODO: Extract from 1Password custom field once we can access it reliably
tower_workspace_id = "59994744926013"

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

# S3 bucket lifecycle configuration for metadata preservation and temporary file cleanup
bucket_lifecycle_configuration = s3.BucketLifecycleConfigurationV2(
    "nf-core-awsmegatests-lifecycle",
    bucket=nf_core_awsmegatests_bucket.id,
    rules=[
        # Rule 1: Preserve metadata files indefinitely (tagged with nextflow.io/metadata=true)
        s3.BucketLifecycleConfigurationV2RuleArgs(
            id="preserve-metadata-files",
            status="Enabled",
            filter=s3.BucketLifecycleConfigurationV2RuleFilterArgs(
                tag=s3.BucketLifecycleConfigurationV2RuleFilterTagArgs(
                    key="nextflow.io/metadata", value="true"
                )
            ),
            transitions=[
                # Transition metadata files to IA after 30 days for cost savings
                s3.BucketLifecycleConfigurationV2RuleTransitionArgs(
                    days=30, storage_class="STANDARD_IA"
                ),
                # Transition to Glacier after 90 days for long-term preservation
                s3.BucketLifecycleConfigurationV2RuleTransitionArgs(
                    days=90, storage_class="GLACIER"
                ),
            ],
            # No expiration for metadata files - preserve indefinitely
        ),
        # Rule 2: Clean up temporary files (tagged with nextflow.io/temporary=true)
        s3.BucketLifecycleConfigurationV2RuleArgs(
            id="cleanup-temporary-files",
            status="Enabled",
            filter=s3.BucketLifecycleConfigurationV2RuleFilterArgs(
                tag=s3.BucketLifecycleConfigurationV2RuleFilterTagArgs(
                    key="nextflow.io/temporary", value="true"
                )
            ),
            expiration=s3.BucketLifecycleConfigurationV2RuleExpirationArgs(
                days=30  # Delete temporary files after 30 days
            ),
        ),
        # Rule 3: Default cleanup for work directory files without tags
        s3.BucketLifecycleConfigurationV2RuleArgs(
            id="cleanup-work-directory",
            status="Enabled",
            filter=s3.BucketLifecycleConfigurationV2RuleFilterArgs(
                prefix="work/"  # Apply to work directory
            ),
            expiration=s3.BucketLifecycleConfigurationV2RuleExpirationArgs(
                days=90  # Delete untagged work files after 90 days
            ),
        ),
        # Rule 4: Cleanup for incomplete multipart uploads
        s3.BucketLifecycleConfigurationV2RuleArgs(
            id="cleanup-incomplete-multipart-uploads",
            status="Enabled",
            abort_incomplete_multipart_upload=s3.BucketLifecycleConfigurationV2RuleAbortIncompleteMultipartUploadArgs(
                days_after_initiation=7
            ),
        ),
    ],
    opts=pulumi.ResourceOptions(
        provider=aws_provider, depends_on=[nf_core_awsmegatests_bucket]
    ),
)

# Export the bucket information
pulumi.export(
    "megatests_bucket",
    {
        "name": nf_core_awsmegatests_bucket.bucket,
        "arn": nf_core_awsmegatests_bucket.arn,
        "region": "eu-west-1",
        "lifecycle_configuration": bucket_lifecycle_configuration.id,
    },
)

# Create TowerForge IAM credentials using the separated module
# Based on https://github.com/seqeralabs/nf-tower-aws
towerforge_access_key_id, towerforge_access_key_secret = create_towerforge_credentials(
    aws_provider, nf_core_awsmegatests_bucket
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
    # Use TowerForge AWS credentials for seqerakit operations (credential separation)
    # These credentials have the specific permissions needed for AWS Batch operations
    "AWS_ACCESS_KEY_ID": towerforge_access_key_id,
    "AWS_SECRET_ACCESS_KEY": towerforge_access_key_secret,
    # Tower CLI configuration - use standard Seqera Cloud endpoint
    "TOWER_API_ENDPOINT": "https://api.cloud.seqera.io",
}

# Read JSON config files to make them dependencies
with open("seqerakit/current-env-cpu.json", "r") as f:
    cpu_config = json.load(f)
with open("seqerakit/current-env-gpu.json", "r") as f:
    gpu_config = json.load(f)
with open("seqerakit/current-env-cpu-arm.json", "r") as f:
    arm_config = json.load(f)

# Deploy CPU environment with seqerakit (with JSON output)
# NOTE: Tower access token needs to be valid and have permissions for nf-core/AWSmegatests workspace
cpu_deploy_cmd = command.local.Command(
    "deploy-cpu-environment",
    create=pulumi.Output.concat(
        "cd seqerakit && uv run seqerakit --json aws_ireland_fusionv2_nvme_cpu_current.yml # Config hash: ",
        str(hash(json.dumps(cpu_config, sort_keys=True))),
    ),
    environment=seqerakit_environment,
    opts=pulumi.ResourceOptions(additional_secret_outputs=["stdout"]),
)

# Deploy GPU environment with seqerakit (with JSON output)
gpu_deploy_cmd = command.local.Command(
    "deploy-gpu-environment",
    create=pulumi.Output.concat(
        "cd seqerakit && uv run seqerakit --json aws_ireland_fusionv2_nvme_gpu_current.yml # Config hash: ",
        str(hash(json.dumps(gpu_config, sort_keys=True))),
    ),
    environment=seqerakit_environment,
    opts=pulumi.ResourceOptions(
        additional_secret_outputs=["stdout"], depends_on=[cpu_deploy_cmd]
    ),
)

# Deploy ARM environment with seqerakit (with JSON output)
arm_deploy_cmd = command.local.Command(
    "deploy-arm-environment",
    create=pulumi.Output.concat(
        "cd seqerakit && uv run seqerakit --json aws_ireland_fusionv2_nvme_cpu_arm_current.yml # Config hash: ",
        str(hash(json.dumps(arm_config, sort_keys=True))),
    ),
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
        # Define known compute environment IDs based on env_name
        known_ids = {
            "cpu": "6G50fuJlfsFPFvu3DfcRbe",  # aws_ireland_fusionv2_nvme_cpu_snapshots
            "gpu": "1txLskDRisZhgizoe5dU5Y",  # aws_ireland_fusionv2_nvme_gpu_snapshots
            "arm": "6q5vq2ow1nvcx3XvLAOUu4",  # aws_ireland_fusionv2_nvme_cpu_ARM_snapshots
        }

        extract_cmd = f"""
        set -e
        
        # Save the output to a temp file for processing
        echo '{seqerakit_output}' > /tmp/seqerakit_output_{env_name}.json
        
        # Check if seqerakit skipped deployment (on_exists: ignore)
        if grep -q "resource already exists and will not be created" /tmp/seqerakit_output_{env_name}.json; then
            # Use known compute environment ID for existing resources
            echo "{known_ids.get(env_name, f"UNKNOWN_ENV_ID_{env_name.upper()}")}"
            exit 0
        fi
        
        # Extract JSON from mixed text/JSON output (redirect debug to stderr)
        JSON_LINE=$(cat /tmp/seqerakit_output_{env_name}.json | grep -E '^\\{{.*\\}}$' | head -1)
        
        if [ -z "$JSON_LINE" ]; then
            # Fallback to known ID if no JSON found
            echo "{known_ids.get(env_name, f"UNKNOWN_ENV_ID_{env_name.upper()}")}"
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
            # Fallback to known ID
            echo "{known_ids.get(env_name, f"UNKNOWN_ENV_ID_{env_name.upper()}")}"
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


# Query existing compute environment IDs directly from Seqera Platform
def create_query_command(env_name: str, grep_pattern: str):
    def create_query_cmd(token: str) -> str:
        return f'tw --access-token="{token}" compute-envs list --workspace=nf-core/AWSmegatests | grep "{grep_pattern}" | awk \'{{print $1}}\''

    return command.local.Command(
        f"query-{env_name}-compute-env",
        create=tower_access_token.apply(create_query_cmd),
        # Remove additional_secret_outputs to make the compute env IDs visible in variables
    )


cpu_query_cmd = create_query_command("cpu", "aws_ireland_fusionv2_nvme_cpu_snapshots")
gpu_query_cmd = create_query_command("gpu", "aws_ireland_fusionv2_nvme_gpu_snapshots")
arm_query_cmd = create_query_command(
    "arm", "aws_ireland_fusionv2_nvme_cpu_ARM_snapshots"
)

# Extract the IDs from the query results
cpu_compute_env_id = cpu_query_cmd.stdout.apply(lambda x: x.strip())
gpu_compute_env_id = gpu_query_cmd.stdout.apply(lambda x: x.strip())
arm_compute_env_id = arm_query_cmd.stdout.apply(lambda x: x.strip())

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

# Legacy compatibility for older nf-core tools templates
# See: https://github.com/nf-core/ops/issues/162
# These duplicate the new variable names into the old secret names expected by nf-core tools v3.3.2 and earlier

# Legacy: TOWER_WORKSPACE_ID as secret (duplicates the variable above)
legacy_workspace_id_secret = github.ActionsOrganizationSecret(
    "legacy-tower-workspace-id",
    visibility="all",
    secret_name="TOWER_WORKSPACE_ID",
    plaintext_value=tower_workspace_id,
    opts=pulumi.ResourceOptions(
        provider=github_provider,
        protect=True,  # Protect from accidental deletion
    ),
)

# Legacy: TOWER_COMPUTE_ENV as secret (points to CPU environment)
legacy_compute_env_secret = github.ActionsOrganizationSecret(
    "legacy-tower-compute-env",
    visibility="all",
    secret_name="TOWER_COMPUTE_ENV",
    plaintext_value=cpu_compute_env_id,
    opts=pulumi.ResourceOptions(
        provider=github_provider,
        protect=True,  # Protect from accidental deletion
    ),
)

# Legacy: AWS_S3_BUCKET as variable
legacy_s3_bucket_variable = github.ActionsOrganizationVariable(
    "legacy-aws-s3-bucket",
    visibility="all",
    variable_name="AWS_S3_BUCKET",
    value="nf-core-awsmegatests",
    opts=pulumi.ResourceOptions(provider=github_provider),
)

# Export the created GitHub resources
pulumi.export(
    "github_resources",
    {
        "variables": {
            "compute_env_cpu": pulumi.Output.unsecret(cpu_variable.value),
            "compute_env_gpu": pulumi.Output.unsecret(gpu_variable.value),
            "compute_env_arm": pulumi.Output.unsecret(arm_variable.value),
            "tower_workspace_id": workspace_id_variable.value,
            "legacy_aws_s3_bucket": legacy_s3_bucket_variable.value,
        },
        "secrets": {
            "tower_access_token": seqera_token_secret.secret_name,
            "legacy_tower_workspace_id": legacy_workspace_id_secret.secret_name,
            "legacy_tower_compute_env": legacy_compute_env_secret.secret_name,
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

# Export TowerForge IAM resources for reference and future use
# Note: Don't call get_towerforge_resources here as it would create duplicate resources
# Instead, create the export dictionary directly
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
