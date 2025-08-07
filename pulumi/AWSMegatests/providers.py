"""Provider configurations for AWS Megatests infrastructure"""

import pulumi_aws as aws
import pulumi_github as github
import pulumi_onepassword as onepassword


def create_providers():
    """Create and configure all required providers"""

    # Configure the 1Password provider to use CLI-based authentication
    # This works with the OP_ACCOUNT environment variable set in .envrc
    onepassword_provider = onepassword.Provider(
        "onepassword-provider",
        account="nf-core",  # Use CLI-based authentication instead of service account token
    )

    # Use default AWS provider which will read from environment variables
    # (set via .envrc with 1Password integration)
    aws_provider = aws.Provider("aws-provider", region="eu-west-1")

    return {
        "onepassword": onepassword_provider,
        "aws": aws_provider,
    }


def create_github_provider(github_token):
    """Create GitHub provider with token (separate to handle dependency)"""
    return github.Provider("github-provider", token=github_token, owner="nf-core")
