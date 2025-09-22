"""AWS provider configuration for AWS Megatests infrastructure."""

import pulumi_aws as aws
from ..utils.constants import AWS_REGION


def create_aws_provider() -> aws.Provider:
    """Create AWS provider using ESC OIDC authentication.

    The ESC environment should automatically provide AWS credentials
    when the environment is imported in Pulumi.prod.yaml.

    Returns:
        aws.Provider: Configured AWS provider instance
    """
    return aws.Provider(
        "aws-provider",
        region=AWS_REGION,
    )
