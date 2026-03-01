"""Third-party integrations for AWS Megatests."""

from .github import create_github_resources
from .github_credentials import create_github_credential, get_github_credential_config

__all__ = [
    "create_github_resources",
    "create_github_credential",
    "get_github_credential_config",
]
