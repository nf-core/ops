"""Configuration management for AWS Megatests infrastructure using Pulumi ESC."""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

from ..utils.constants import DEFAULT_ENV_VARS


class ConfigurationError(Exception):
    """Exception raised when configuration validation fails."""

    pass


@dataclass
class InfrastructureConfig:
    """Typed configuration for AWS Megatests infrastructure.

    Attributes:
        tower_access_token: Seqera Platform access token
        tower_workspace_id: Seqera Platform workspace ID
        github_token: GitHub personal access token (classic)
        platform_github_org_token: GitHub fine-grained token to avoid rate limits when pulling pipelines
    """

    tower_access_token: Optional[str]
    tower_workspace_id: str
    github_token: Optional[str]
    platform_github_org_token: Optional[str]

    def validate(self) -> None:
        """Validate configuration values.

        Raises:
            ConfigurationError: If required configuration is missing or invalid
        """
        missing_vars = []

        if not self.tower_access_token:
            missing_vars.append("TOWER_ACCESS_TOKEN")

        if not self.github_token:
            missing_vars.append("GITHUB_TOKEN")

        # Validate workspace ID is numeric
        if (
            not self.tower_workspace_id
            or not self.tower_workspace_id.replace(".", "").isdigit()
        ):
            missing_vars.append("TOWER_WORKSPACE_ID (must be numeric)")

        if missing_vars:
            raise ConfigurationError(
                f"Missing or invalid required environment variables: {', '.join(missing_vars)}. "
                "Please ensure these are set in your ESC environment."
            )


def _get_env_var_with_fallback(
    var_name: str, fallback: Optional[str] = None
) -> Optional[str]:
    """Get environment variable with optional fallback.

    Args:
        var_name: Name of the environment variable
        fallback: Optional fallback value if variable is not set

    Returns:
        Optional[str]: Environment variable value or fallback
    """
    value = os.environ.get(var_name)
    if not value and fallback:
        print(
            f"Warning: {var_name} not found in ESC environment, using fallback: {fallback}"
        )
        return fallback
    return value


def get_configuration() -> Dict[str, Any]:
    """Get configuration values from ESC environment variables.

    All configuration comes from ESC environment variables which are automatically
    set when the ESC environment is imported.

    Returns:
        Dict[str, Any]: Configuration dictionary compatible with existing code

    Raises:
        ConfigurationError: If required configuration is missing or invalid
    """
    # Get workspace ID from environment or fall back to default
    workspace_id = _get_env_var_with_fallback(
        "TOWER_WORKSPACE_ID", DEFAULT_ENV_VARS.get("TOWER_WORKSPACE_ID")
    )

    # Create typed configuration object
    config = InfrastructureConfig(
        tower_access_token=os.environ.get("TOWER_ACCESS_TOKEN"),
        tower_workspace_id=workspace_id or "",
        github_token=os.environ.get("GITHUB_TOKEN"),
        platform_github_org_token=os.environ.get("PLATFORM_GITHUB_ORG_TOKEN"),
    )

    # Validate configuration
    config.validate()

    # Return dictionary format for backward compatibility
    return {
        "tower_access_token": config.tower_access_token,
        "tower_workspace_id": config.tower_workspace_id,
        "github_token": config.github_token,
        "platform_github_org_token": config.platform_github_org_token,
        # AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN)
        # are automatically handled by ESC and picked up by the AWS provider
    }
