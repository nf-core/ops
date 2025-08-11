"""GitHub integration for AWS Megatests - secrets and variables management"""

import pulumi
import pulumi_github as github


def create_github_resources(
    github_provider, compute_env_ids, tower_workspace_id, tower_access_token=None
):
    """Create GitHub organization variables and provide manual secret commands

    Args:
        github_provider: GitHub provider instance
        compute_env_ids: Dictionary containing compute environment IDs
        tower_workspace_id: Seqera Platform workspace ID
        tower_access_token: Tower access token for manual secret commands (optional)
    """

    # Create org-level GitHub variables for compute environment IDs (non-sensitive)
    # Using delete_before_replace to work around pulumi/pulumi-github#250
    # Additional protection against 409 conflicts with ignore_changes for existing variables
    cpu_variable = github.ActionsOrganizationVariable(
        "tower-compute-env-cpu",
        visibility="all",
        variable_name="TOWER_COMPUTE_ENV_CPU",
        value=compute_env_ids["cpu"],
        opts=pulumi.ResourceOptions(
            provider=github_provider,
            delete_before_replace=True,  # Workaround for GitHub provider issue #250
            ignore_changes=[
                "visibility"
            ],  # Ignore changes to visibility if variable exists
        ),
    )

    gpu_variable = github.ActionsOrganizationVariable(
        "tower-compute-env-gpu",
        visibility="all",
        variable_name="TOWER_COMPUTE_ENV_GPU",
        value=compute_env_ids["gpu"],
        opts=pulumi.ResourceOptions(
            provider=github_provider,
            delete_before_replace=True,  # Workaround for GitHub provider issue #250
            ignore_changes=[
                "visibility"
            ],  # Ignore changes to visibility if variable exists
        ),
    )

    arm_variable = github.ActionsOrganizationVariable(
        "tower-compute-env-arm",
        visibility="all",
        variable_name="TOWER_COMPUTE_ENV_ARM",
        value=compute_env_ids["arm"],
        opts=pulumi.ResourceOptions(
            provider=github_provider,
            delete_before_replace=True,  # Workaround for GitHub provider issue #250
            ignore_changes=[
                "visibility"
            ],  # Ignore changes to visibility if variable exists
        ),
    )

    # Create org-level GitHub variable for workspace ID (non-sensitive)
    workspace_id_variable = github.ActionsOrganizationVariable(
        "tower-workspace-id",
        visibility="all",
        variable_name="TOWER_WORKSPACE_ID",
        value=tower_workspace_id,
        opts=pulumi.ResourceOptions(
            provider=github_provider,
            delete_before_replace=True,  # Workaround for GitHub provider issue #250
            ignore_changes=[
                "visibility"
            ],  # Ignore changes to visibility if variable exists
        ),
    )

    # Legacy: AWS_S3_BUCKET as variable - MANAGED EXTERNALLY
    # This variable already exists in the GitHub organization and is managed outside of Pulumi
    # Value: "nf-core-awsmegatests" - no Pulumi management needed

    variables = {
        "cpu": cpu_variable,
        "gpu": gpu_variable,
        "arm": arm_variable,
        "workspace_id": workspace_id_variable,
        # legacy_s3_bucket: managed externally, already exists
    }

    # GitHub Secrets Management - Manual Commands Only
    # NOTE: Due to pulumi/pulumi-github#250, secrets must be managed manually
    # https://github.com/nf-core/ops/issues/162 - Legacy compatibility needed

    # Generate manual gh CLI commands for secrets management
    def create_gh_commands(workspace_id_val, cpu_env_id_val, tower_token_val=None):
        commands = []

        # Legacy workspace ID secret
        commands.append(
            f'gh secret set TOWER_WORKSPACE_ID --org nf-core --body "{workspace_id_val}" --visibility all'
        )

        # Legacy compute env secret (CPU)
        commands.append(
            f'gh secret set TOWER_COMPUTE_ENV --org nf-core --body "{cpu_env_id_val}" --visibility all'
        )

        # Tower access token (if provided)
        if tower_token_val:
            commands.append(
                "OP_ACCOUNT=nf-core gh secret set TOWER_ACCESS_TOKEN --org nf-core --body \"$(op read 'op://Dev/Seqera Platform/TOWER_ACCESS_TOKEN')\" --visibility all"
            )

        return commands

    # Generate commands with resolved values
    if all(isinstance(compute_env_ids[k], str) for k in compute_env_ids) and isinstance(
        tower_workspace_id, str
    ):
        # All static values
        gh_cli_commands = create_gh_commands(
            tower_workspace_id,
            compute_env_ids["cpu"],
            "<TOWER_ACCESS_TOKEN>" if tower_access_token else None,
        )
    else:
        # Dynamic values - create commands that will be resolved at runtime
        gh_cli_commands = pulumi.Output.all(
            workspace_id=tower_workspace_id, cpu_env_id=compute_env_ids["cpu"]
        ).apply(
            lambda args: create_gh_commands(
                args["workspace_id"],
                args["cpu_env_id"],
                "<TOWER_ACCESS_TOKEN>" if tower_access_token else None,
            )
        )

    return {
        "variables": variables,
        "secrets": {},  # No Pulumi-managed secrets due to provider issue
        "gh_cli_commands": gh_cli_commands,
        "note": "Secrets must be managed manually due to pulumi/pulumi-github#250",
    }
