"""AWS provider configuration for iGenomes infrastructure."""

import pulumi_aws as aws
from typing import Dict, Any

from ..utils.constants import S3_REGION


def create_aws_provider(config: Dict[str, Any]) -> aws.Provider:
    """Create and configure AWS provider.

    Args:
        config: Configuration dictionary with AWS credentials

    Returns:
        aws.Provider: Configured AWS provider instance
    """
    return aws.Provider(
        "aws-igenomes",
        region=config.get("aws_region", S3_REGION),
        access_key=config["aws_access_key_id"],
        secret_key=config["aws_secret_access_key"],
        # Skip credentials validation if we only have read-only access
        skip_credentials_validation=False,
        skip_requesting_account_id=False,
    )
