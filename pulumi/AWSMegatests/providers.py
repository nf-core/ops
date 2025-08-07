"""Provider configurations for AWS Megatests infrastructure"""

import pulumi
import pulumi_aws as aws
import pulumi_github as github
import pulumi_onepassword as onepassword


def create_providers():
    """Create and configure all required providers"""

    # Configure the 1Password provider using service account token from Pulumi config
    # This avoids dependency on environment variables and direnv
    onepassword_config = pulumi.Config("pulumi-onepassword")
    onepassword_provider = onepassword.Provider(
        "onepassword-provider-v2",
        service_account_token=onepassword_config.require_secret(
            "service_account_token"
        ),
    )

    return {
        "onepassword": onepassword_provider,
    }


def create_aws_provider(aws_access_key_id, aws_secret_access_key):
    """Create AWS provider with credentials from 1Password"""
    return aws.Provider(
        "aws-provider",
        region="eu-west-1",
        access_key=aws_access_key_id,
        secret_key=aws_secret_access_key,
    )


def create_github_provider(github_token):
    """Create GitHub provider with token (separate to handle dependency)"""
    return github.Provider("github-provider", token=github_token, owner="nf-core")
