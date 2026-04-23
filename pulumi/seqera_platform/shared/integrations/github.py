"""GitHub integration for AWS Megatests - secrets and variables management."""

from typing import Dict, Any, List, Optional, Union

import pulumi
import pulumi_github as github

from utils.constants import GITHUB_VARIABLE_NAMES, S3_BUCKET_NAME


class GitHubIntegrationError(Exception):
    """Exception raised when GitHub integration operations fail."""

    pass


def _create_organization_variable(
    provider: github.Provider,
    resource_name: str,
    variable_name: str,
    value: Union[str, pulumi.Output[str]],
) -> github.ActionsOrganizationVariable:
    """Create a GitHub organization variable with consistent configuration.

    Args:
        provider: GitHub provider instance
        resource_name: Pulumi resource name
        variable_name: GitHub variable name
        value: Variable value

    Returns:
        github.ActionsOrganizationVariable: Created variable resource
    """
    return github.ActionsOrganizationVariable(
        resource_name,
        visibility="all",
        variable_name=variable_name,
        value=value,
        opts=pulumi.ResourceOptions(
            provider=provider,
            delete_before_replace=True,  # Workaround for GitHub provider issue #250
            ignore_changes=[
                "visibility"
            ],  # Ignore changes to visibility if variable exists
        ),
    )


def _create_gh_commands(
    workspace_id_val: str, cpu_env_id_val: str, tower_token_val: Optional[str] = None
) -> List[str]:
    """Generate manual gh CLI commands for secrets management.

    Args:
        workspace_id_val: Workspace ID value
        cpu_env_id_val: CPU environment ID value
        tower_token_val: Optional tower access token placeholder

    Returns:
        List[str]: List of gh CLI commands
    """
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
            "OP_ACCOUNT=nf-core gh secret set TOWER_ACCESS_TOKEN --org nf-core "
            "--body \"$(op read 'op://Dev/Seqera Platform/TOWER_ACCESS_TOKEN')\" --visibility all"
        )

    return commands


def create_github_resources(
    github_provider: github.Provider,
    compute_env_ids: Dict[str, Any],
    tower_workspace_id: Union[str, pulumi.Output[str]],
    tower_access_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Create GitHub organization variables and provide manual secret commands.

    Args:
        github_provider: GitHub provider instance
        compute_env_ids: Dictionary containing compute environment IDs
        tower_workspace_id: Seqera Platform workspace ID
        tower_access_token: Tower access token for manual secret commands (optional)

    Returns:
        Dict[str, Any]: Dictionary containing created variables and manual commands

    Raises:
        GitHubIntegrationError: If GitHub resource creation fails
    """
    # Create org-level GitHub variables for compute environment IDs (non-sensitive)
    # Using delete_before_replace to work around pulumi/pulumi-github#250
    variables = {}

    # Compute environment variables
    for env_type in ["cpu", "gpu", "arm"]:
        var_name = GITHUB_VARIABLE_NAMES[env_type]
        resource_name = f"tower-compute-env-{env_type}"

        variables[env_type] = _create_organization_variable(
            github_provider,
            resource_name,
            var_name,
            compute_env_ids[env_type],
        )

    # Workspace ID variable
    variables["workspace_id"] = _create_organization_variable(
        github_provider,
        "tower-workspace-id",
        GITHUB_VARIABLE_NAMES["workspace_id"],
        tower_workspace_id,
    )

    # Legacy S3 bucket variable
    variables["legacy_s3_bucket"] = _create_organization_variable(
        github_provider,
        "legacy-aws-s3-bucket",
        GITHUB_VARIABLE_NAMES["s3_bucket"],
        S3_BUCKET_NAME,
    )

    # GitHub Secrets Management - Manual Commands Only
    # NOTE: Due to pulumi/pulumi-github#250, secrets must be managed manually
    # https://github.com/nf-core/ops/issues/162 - Legacy compatibility needed

    # Generate manual gh CLI commands for secrets management
    if all(isinstance(compute_env_ids[k], str) for k in compute_env_ids) and isinstance(
        tower_workspace_id, str
    ):
        # All static values
        gh_cli_commands: Union[List[str], pulumi.Output[List[str]]] = (
            _create_gh_commands(
                tower_workspace_id,
                compute_env_ids["cpu"],
                "<TOWER_ACCESS_TOKEN>" if tower_access_token else None,
            )
        )
    else:
        # Dynamic values - create commands that will be resolved at runtime
        gh_cli_commands = pulumi.Output.all(
            workspace_id=tower_workspace_id, cpu_env_id=compute_env_ids["cpu"]
        ).apply(
            lambda args: _create_gh_commands(
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
