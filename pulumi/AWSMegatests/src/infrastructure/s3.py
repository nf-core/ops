"""S3 infrastructure management for AWS Megatests."""

from typing import Dict, Any, Optional

import pulumi
from pulumi_aws import s3

from ..utils.constants import S3_BUCKET_NAME


def create_s3_infrastructure(aws_provider) -> Dict[str, Any]:
    """Create S3 bucket and lifecycle configuration.

    Args:
        aws_provider: Configured AWS provider instance

    Returns:
        Dict[str, Any]: Dictionary containing bucket and lifecycle configuration
    """
    # Import existing AWS resources used by nf-core megatests
    # S3 bucket for Nextflow work directory (already exists)
    nf_core_awsmegatests_bucket = s3.Bucket(
        "nf-core-awsmegatests",
        bucket=S3_BUCKET_NAME,
        opts=pulumi.ResourceOptions(
            import_=S3_BUCKET_NAME,  # Import existing bucket
            protect=True,  # Protect from accidental deletion
            provider=aws_provider,  # Use configured AWS provider
            ignore_changes=[
                "cors_rules",
                "lifecycle_rules",
                "versioning",
            ],  # Don't modify existing configurations - managed manually due to permission constraints
        ),
    )

    # S3 bucket lifecycle configuration
    # NOTE: Lifecycle rules are managed manually due to AWS permission constraints
    # See S3_LIFECYCLE_RULES.md for the complete configuration that needs to be applied
    # Current AWS credentials don't have s3:PutLifecycleConfiguration permission
    #
    # The lifecycle configuration includes rules for:
    # - Automatic cleanup of work/ and scratch/ directories (30 days)
    # - Preservation of log files (tagged with nextflow.io/log=true)
    # - Cost optimization through storage class transitions

    # Placeholder for lifecycle configuration (managed externally)
    # This ensures the bucket resource exists for other dependencies
    bucket_lifecycle_configuration: Optional[Any] = None

    return {
        "bucket": nf_core_awsmegatests_bucket,
        "lifecycle_configuration": bucket_lifecycle_configuration,
    }
