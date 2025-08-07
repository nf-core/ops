"""GitHub integration for AWS Megatests - secrets and variables management"""

import pulumi
import pulumi_github as github


def create_github_resources(github_provider, compute_env_ids, tower_workspace_id):
    """Create GitHub organization secrets and variables"""

    # Create org-level GitHub variables for compute environment IDs (non-sensitive)
    cpu_variable = github.ActionsOrganizationVariable(
        "tower-compute-env-cpu",
        visibility="all",
        variable_name="TOWER_COMPUTE_ENV_CPU",
        value=compute_env_ids["cpu"],
        opts=pulumi.ResourceOptions(provider=github_provider),
    )

    gpu_variable = github.ActionsOrganizationVariable(
        "tower-compute-env-gpu",
        visibility="all",
        variable_name="TOWER_COMPUTE_ENV_GPU",
        value=compute_env_ids["gpu"],
        opts=pulumi.ResourceOptions(provider=github_provider),
    )

    arm_variable = github.ActionsOrganizationVariable(
        "tower-compute-env-arm",
        visibility="all",
        variable_name="TOWER_COMPUTE_ENV_ARM",
        value=compute_env_ids["arm"],
        opts=pulumi.ResourceOptions(provider=github_provider),
    )

    # GitHub organization secret for Seqera Platform API token must be managed manually
    # due to GitHub permission requirements (org admin or actions secrets fine-grained permission)
    #
    # To set the secret manually, use:
    # gh secret set TOWER_ACCESS_TOKEN --org nf-core --body "$TOWER_ACCESS_TOKEN"
    #
    # This secret was removed from Pulumi management to avoid 403 permission errors:
    # "403 You must be an org admin or have the actions secrets fine-grained permission"

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
        plaintext_value=compute_env_ids["cpu"],
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

    return {
        "variables": {
            "cpu": cpu_variable,
            "gpu": gpu_variable,
            "arm": arm_variable,
            "workspace_id": workspace_id_variable,
            "legacy_s3_bucket": legacy_s3_bucket_variable,
        },
        "secrets": {
            "legacy_workspace_id": legacy_workspace_id_secret,
            "legacy_compute_env": legacy_compute_env_secret,
        },
    }
