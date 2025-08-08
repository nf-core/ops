"""GitHub integration for AWS Megatests - secrets and variables management"""

import pulumi
import pulumi_github as github
import pulumi_command as command
import json


def create_github_resources(github_provider, compute_env_ids, tower_workspace_id, tower_access_token=None, enable_gh_cli_fallback=True):
    """Create GitHub organization secrets and variables
    
    Args:
        github_provider: GitHub provider instance
        compute_env_ids: Dictionary containing compute environment IDs 
        tower_workspace_id: Seqera Platform workspace ID
        tower_access_token: Tower access token for secrets (optional)
        enable_gh_cli_fallback: Enable gh CLI fallback for secrets management
    """

    # Create org-level GitHub variables for compute environment IDs (non-sensitive)
    # Using delete_before_replace to work around pulumi/pulumi-github#250
    cpu_variable = github.ActionsOrganizationVariable(
        "tower-compute-env-cpu",
        visibility="all",
        variable_name="TOWER_COMPUTE_ENV_CPU",
        value=compute_env_ids["cpu"],
        opts=pulumi.ResourceOptions(
            provider=github_provider,
            delete_before_replace=True,  # Workaround for GitHub provider issue #250
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
        ),
    )

    # Legacy: AWS_S3_BUCKET as variable
    legacy_s3_bucket_variable = github.ActionsOrganizationVariable(
        "legacy-aws-s3-bucket",
        visibility="all",
        variable_name="AWS_S3_BUCKET",
        value="nf-core-awsmegatests",
        opts=pulumi.ResourceOptions(
            provider=github_provider,
            delete_before_replace=True,  # Workaround for GitHub provider issue #250
        ),
    )

    variables = {
        "cpu": cpu_variable,
        "gpu": gpu_variable,
        "arm": arm_variable,
        "workspace_id": workspace_id_variable,
        "legacy_s3_bucket": legacy_s3_bucket_variable,
    }

    # GitHub Secrets Management
    # NOTE: Due to pulumi/pulumi-github#250, we use gh CLI fallback for secrets
    # https://github.com/nf-core/ops/issues/162 - Legacy compatibility needed
    
    secrets = {}
    gh_cli_commands = []
    
    # Try Pulumi-managed secrets first with delete_before_replace workaround
    if not enable_gh_cli_fallback:
        try:
            # Legacy: TOWER_WORKSPACE_ID as secret (duplicates the variable above)
            legacy_workspace_id_secret = github.ActionsOrganizationSecret(
                "legacy-tower-workspace-id",
                visibility="all",
                secret_name="TOWER_WORKSPACE_ID",
                plaintext_value=tower_workspace_id,
                opts=pulumi.ResourceOptions(
                    provider=github_provider,
                    delete_before_replace=True,  # Workaround for GitHub provider issue #250
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
                    delete_before_replace=True,  # Workaround for GitHub provider issue #250
                    protect=True,  # Protect from accidental deletion
                ),
            )

            secrets = {
                "legacy_workspace_id": legacy_workspace_id_secret,
                "legacy_compute_env": legacy_compute_env_secret,
            }
        except Exception as e:
            pulumi.log.warn(f"Pulumi GitHub secrets failed, falling back to gh CLI: {e}")
            enable_gh_cli_fallback = True
    
    # GitHub CLI fallback for secrets (more reliable)
    if enable_gh_cli_fallback:
        pulumi.log.info("Using gh CLI fallback for GitHub secrets management")
        
        # Generate dynamic gh CLI commands with actual values
        def create_gh_commands(workspace_id_val, cpu_env_id_val, tower_token_val=None):
            commands = []
            
            # Legacy workspace ID secret
            commands.append(f'gh secret set TOWER_WORKSPACE_ID --org nf-core --body "{workspace_id_val}"')
            
            # Legacy compute env secret (CPU)
            commands.append(f'gh secret set TOWER_COMPUTE_ENV --org nf-core --body "{cpu_env_id_val}"')
            
            # Tower access token (if provided)
            if tower_token_val:
                commands.append('gh secret set TOWER_ACCESS_TOKEN --org nf-core --body "$TOWER_ACCESS_TOKEN"')
            
            return commands
        
        # Generate commands with resolved values
        if isinstance(tower_workspace_id, str):
            # Static value
            workspace_id_resolved = tower_workspace_id
        else:
            # Pulumi Output - need to apply
            workspace_id_resolved = tower_workspace_id
        
        # Create command list based on compute env IDs
        if all(isinstance(compute_env_ids[k], str) for k in compute_env_ids):
            # All static values
            gh_cli_commands = create_gh_commands(
                workspace_id_resolved, 
                compute_env_ids["cpu"],
                tower_access_token
            )
        else:
            # Dynamic values - create commands that will be resolved at runtime
            gh_cli_commands = pulumi.Output.all(
                workspace_id=tower_workspace_id,
                cpu_env_id=compute_env_ids["cpu"],
                tower_token=tower_access_token
            ).apply(
                lambda args: create_gh_commands(
                    args["workspace_id"], 
                    args["cpu_env_id"], 
                    args["tower_token"]
                )
            )

    return {
        "variables": variables,
        "secrets": secrets,
        "gh_cli_commands": gh_cli_commands,
        "using_gh_cli_fallback": enable_gh_cli_fallback,
    }


def execute_github_cli_fallback(gh_commands, tower_access_token=None):
    """Execute GitHub CLI commands as fallback for secrets management
    
    Args:
        gh_commands: List of gh CLI commands or Pulumi Output containing commands
        tower_access_token: Tower access token to set as environment variable
    
    Returns:
        Command resource for executing the gh CLI commands
    """
    
    # Set up environment for gh CLI
    env_vars = {
        "GH_TOKEN": "$GITHUB_TOKEN",  # Assumes GITHUB_TOKEN is available in environment
    }
    
    if tower_access_token:
        if isinstance(tower_access_token, str):
            env_vars["TOWER_ACCESS_TOKEN"] = tower_access_token
        else:
            # For Pulumi Output, we need to handle it differently
            env_vars["TOWER_ACCESS_TOKEN"] = tower_access_token
    
    # Create command to execute gh CLI secrets
    if isinstance(gh_commands, list):
        # Static command list
        command_script = " && ".join(gh_commands)
    else:
        # Pulumi Output - need to apply
        command_script = gh_commands.apply(lambda cmds: " && ".join(cmds))
    
    gh_cli_cmd = command.local.Command(
        "github-secrets-cli-fallback",
        create=pulumi.Output.concat(
            "echo 'Setting GitHub secrets via gh CLI...' && ",
            command_script,
            " && echo 'GitHub secrets updated successfully'"
        ),
        environment=env_vars,
        opts=pulumi.ResourceOptions(
            additional_secret_outputs=["environment", "create"],
        ),
    )
    
    return gh_cli_cmd
