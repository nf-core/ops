"""GitHub provider configuration for AWS Megatests infrastructure."""

import pulumi_github as github
from ..utils.constants import GITHUB_ORG


def create_github_provider(github_token: str) -> github.Provider:
    """Create GitHub provider with token authentication.

    Args:
        github_token: GitHub personal access token with org admin permissions

    Returns:
        github.Provider: Configured GitHub provider instance
    """
    return github.Provider("github-provider", token=github_token, owner=GITHUB_ORG)
