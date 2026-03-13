"""S3 infrastructure management for iGenomes bucket.

This module handles importing and managing the ngi-igenomes S3 bucket.
The bucket is part of AWS Open Data Registry and may have limited write permissions.
"""

from typing import Dict, Any
import pulumi
from pulumi_aws import s3

from ..utils.constants import (
    S3_BUCKET_NAME,
    S3_REGION,
    IGENOMES_DESCRIPTION,
    DEFAULT_TAGS,
)


def import_igenomes_bucket(aws_provider: Any) -> Dict[str, Any]:
    """Import the existing ngi-igenomes S3 bucket into Pulumi state.

    The ngi-igenomes bucket is hosted by AWS Open Data Registry.
    This function imports the bucket for tracking and reference purposes.

    Note: Write permissions may be limited. Use ignore_changes for
    properties we cannot manage.

    Args:
        aws_provider: Configured AWS provider instance

    Returns:
        Dict[str, Any]: Dictionary containing bucket and related resources
    """
    # Import existing ngi-igenomes bucket
    igenomes_bucket = s3.Bucket(
        "ngi-igenomes",
        bucket=S3_BUCKET_NAME,
        opts=pulumi.ResourceOptions(
            import_=S3_BUCKET_NAME,  # Import from existing bucket
            protect=True,  # Protect from accidental deletion
            provider=aws_provider,
            # Ignore changes to properties we likely can't manage
            ignore_changes=[
                "lifecycle_rules",
                "versioning",
                "acl",
                "grant",
                "logging",
                "object_lock_configuration",
                "policy",
                "replication_configuration",
                "server_side_encryption_configuration",
                "website",
                "cors_rule",
                "acceleration_status",
                "request_payer",
            ],
        ),
    )

    # Attempt to import bucket versioning configuration
    # This may fail if we don't have permissions
    try:
        bucket_versioning = s3.BucketVersioningV2(
            "ngi-igenomes-versioning",
            bucket=igenomes_bucket.id,
            opts=pulumi.ResourceOptions(
                provider=aws_provider,
                depends_on=[igenomes_bucket],
                # Import if exists, otherwise create won't work without permissions
                delete_before_replace=False,
                ignore_changes=["versioning_configuration"],
            ),
        )
    except Exception as e:
        pulumi.log.warn(f"Could not import bucket versioning: {e}")
        bucket_versioning = None

    # Attempt to import public access block configuration
    try:
        public_access_block = s3.BucketPublicAccessBlock(
            "ngi-igenomes-public-access",
            bucket=igenomes_bucket.id,
            opts=pulumi.ResourceOptions(
                provider=aws_provider,
                depends_on=[igenomes_bucket],
                delete_before_replace=False,
                ignore_changes=[
                    "block_public_acls",
                    "block_public_policy",
                    "ignore_public_acls",
                    "restrict_public_buckets",
                ],
            ),
        )
    except Exception as e:
        pulumi.log.warn(f"Could not import public access block: {e}")
        public_access_block = None

    return {
        "bucket": igenomes_bucket,
        "versioning": bucket_versioning,
        "public_access_block": public_access_block,
    }


def get_bucket_metadata() -> Dict[str, Any]:
    """Get metadata about the iGenomes bucket.

    Returns:
        Dict[str, Any]: Bucket metadata and documentation
    """
    return {
        "name": S3_BUCKET_NAME,
        "region": S3_REGION,
        "description": IGENOMES_DESCRIPTION,
        "access": "public-read (no authentication required)",
        "registry": "AWS Open Data Registry",
        "documentation": "https://ewels.github.io/AWS-iGenomes/",
        "github": "https://github.com/ewels/AWS-iGenomes",
        "usage": {
            "s3_uri": f"s3://{S3_BUCKET_NAME}",
            "https_url": f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com",
            "cli_example": f"aws s3 --no-sign-request --region {S3_REGION} ls s3://{S3_BUCKET_NAME}/",
            "nextflow_config": f'params.igenomes_base = "s3://{S3_BUCKET_NAME}/igenomes"',
        },
        "tags": DEFAULT_TAGS,
    }
