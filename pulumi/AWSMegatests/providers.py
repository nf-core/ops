"""Provider configurations for AWS Megatests infrastructure"""

import pulumi_aws as aws
import pulumi_github as github


def create_aws_provider():
    """Create AWS provider using ESC OIDC authentication"""
    # ESC environment should automatically provide AWS credentials
    # when the environment is imported in Pulumi.prod.yaml
    return aws.Provider(
        "aws-provider",
        region="eu-west-1",
    )


def create_github_provider(github_token):
    """Create GitHub provider with token"""
    return github.Provider("github-provider", token=github_token, owner="nf-core")
