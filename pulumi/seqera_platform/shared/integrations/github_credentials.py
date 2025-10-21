"""GitHub credentials integration for Seqera Platform."""

import pulumi
import pulumi_seqera as seqera
from typing import Dict, Tuple


class GitHubCredentialError(Exception):
    """Exception raised when GitHub credential creation fails."""

    pass


def create_github_credential(
    seqera_provider: seqera.Provider,
    workspace_id: int,
    github_token: str,
    github_username: str = "nf-core-bot",
    credential_name: str = "nf-core-github-finegrained",
) -> Tuple[seqera.Credential, str]:
    """Create a GitHub fine-grained credential in Seqera Platform.

    This credential allows Seqera Platform to pull pipeline repositories from GitHub
    without hitting GitHub rate limits. The fine-grained token provides secure,
    scoped access to nf-core repositories with minimal required permissions.

    Args:
        seqera_provider: Configured Seqera provider instance
        workspace_id: Seqera workspace ID
        github_token: Fine-grained GitHub personal access token for repository access
        github_username: GitHub username (default: nf-core-bot)
        credential_name: Name for the credential in Seqera

    Returns:
        Tuple of (credential_resource, credential_id)

    Raises:
        GitHubCredentialError: If credential creation fails
        ValueError: If required parameters are missing
    """
    # Validate required parameters
    if not github_token:
        raise ValueError("GitHub token is required")
    if not workspace_id:
        raise ValueError("Workspace ID is required")

    pulumi.log.info(
        f"Creating GitHub credential '{credential_name}' in workspace {workspace_id}"
    )

    try:
        # Create GitHub credential using Seqera Terraform provider
        github_credential = seqera.Credential(
            f"github-credential-{credential_name}",
            name=credential_name,
            description="Fine-grained GitHub token to avoid rate limits when Platform pulls pipeline repositories",
            provider_type="github",
            base_url="https://github.com/nf-core/",  # Scope to nf-core organization
            keys=seqera.CredentialKeysArgs(
                github=seqera.CredentialKeysGithubArgs(
                    username=github_username,
                    password=github_token,  # GitHub tokens go in the password field
                )
            ),
            workspace_id=workspace_id,
            opts=pulumi.ResourceOptions(
                provider=seqera_provider,
                protect=True,  # Protect credential from accidental deletion
            ),
        )

        # Return both the resource and the credential ID for reference
        return github_credential, github_credential.id

    except Exception as e:
        pulumi.log.error(f"Failed to create GitHub credential: {str(e)}")
        raise GitHubCredentialError(
            f"GitHub credential creation failed: {str(e)}"
        ) from e


def get_github_credential_config() -> Dict[str, str]:
    """Get configuration for GitHub credential creation.

    Returns:
        Dict containing configuration values from ESC environment
    """
    import os

    return {
        "github_finegrained_token": os.environ.get("PLATFORM_GITHUB_ORG_TOKEN", ""),
        "github_username": os.environ.get("GITHUB_USERNAME", "nf-core-bot"),
        "credential_name": os.environ.get(
            "GITHUB_CREDENTIAL_NAME", "nf-core-github-finegrained"
        ),
    }
