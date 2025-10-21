"""S3 infrastructure management for AWS Megatests."""

from typing import Dict, Any

import pulumi
from pulumi_aws import s3

from utils.constants import S3_BUCKET_NAME


def create_s3_infrastructure(aws_provider, bucket_name: str = None, import_existing: bool = True) -> Dict[str, Any]:
    """Create or import S3 bucket and lifecycle configuration.

    Args:
        aws_provider: Configured AWS provider instance
        bucket_name: Optional bucket name override. If not provided, uses S3_BUCKET_NAME from constants
        import_existing: If True, import existing bucket. If False, create new bucket.

    Returns:
        Dict[str, Any]: Dictionary containing bucket and lifecycle configuration
    """
    # Use provided bucket name or fall back to constant
    actual_bucket_name = bucket_name or S3_BUCKET_NAME

    # Create resource options based on whether we're importing or creating
    if import_existing:
        # Import existing AWS resources (for legacy workspaces)
        resource_opts = pulumi.ResourceOptions(
            import_=actual_bucket_name,  # Import existing bucket
            protect=True,  # Protect from accidental deletion
            provider=aws_provider,  # Use configured AWS provider
            ignore_changes=[
                "lifecycle_rules",
                "versioning",
            ],  # Don't modify existing configurations - managed manually due to permission constraints
        )
    else:
        # Create new bucket
        resource_opts = pulumi.ResourceOptions(
            protect=True,  # Protect from accidental deletion
            provider=aws_provider,  # Use configured AWS provider
        )

    # S3 bucket for Nextflow work directory
    nf_core_awsmegatests_bucket = s3.Bucket(
        actual_bucket_name,
        bucket=actual_bucket_name,
        opts=resource_opts,
    )

    # S3 bucket lifecycle configuration
    # Create lifecycle rules for automated cost optimization and cleanup
    bucket_lifecycle_configuration = create_s3_lifecycle_configuration(
        aws_provider, nf_core_awsmegatests_bucket
    )

    # S3 bucket CORS configuration for Seqera Data Explorer compatibility
    bucket_cors_configuration = create_s3_cors_configuration(
        aws_provider, nf_core_awsmegatests_bucket
    )

    return {
        "bucket": nf_core_awsmegatests_bucket,
        "lifecycle_configuration": bucket_lifecycle_configuration,
        "cors_configuration": bucket_cors_configuration,
    }


def create_s3_lifecycle_configuration(aws_provider, bucket):
    """Create S3 lifecycle configuration with proper rules for Nextflow workflows.

    Args:
        aws_provider: Configured AWS provider instance
        bucket: S3 bucket resource

    Returns:
        S3 bucket lifecycle configuration resource
    """
    # S3 bucket lifecycle configuration for cost optimization and cleanup
    # Rules designed specifically for Nextflow workflow patterns
    lifecycle_configuration = s3.BucketLifecycleConfigurationV2(
        "nf-core-awsmegatests-lifecycle",
        bucket=bucket.id,
        rules=[
            # Rule 1: Preserve metadata files with cost optimization
            s3.BucketLifecycleConfigurationV2RuleArgs(
                id="preserve-metadata-files",
                status="Enabled",
                filter=s3.BucketLifecycleConfigurationV2RuleFilterArgs(
                    tag=s3.BucketLifecycleConfigurationV2RuleFilterTagArgs(
                        key="nextflow.io/metadata", value="true"
                    )
                ),
                transitions=[
                    s3.BucketLifecycleConfigurationV2RuleTransitionArgs(
                        days=30, storage_class="STANDARD_IA"
                    ),
                    s3.BucketLifecycleConfigurationV2RuleTransitionArgs(
                        days=90, storage_class="GLACIER"
                    ),
                ],
            ),
            # Rule 2: Clean up temporary files after 30 days
            s3.BucketLifecycleConfigurationV2RuleArgs(
                id="cleanup-temporary-files",
                status="Enabled",
                filter=s3.BucketLifecycleConfigurationV2RuleFilterArgs(
                    tag=s3.BucketLifecycleConfigurationV2RuleFilterTagArgs(
                        key="nextflow.io/temporary", value="true"
                    )
                ),
                expiration=s3.BucketLifecycleConfigurationV2RuleExpirationArgs(days=30),
            ),
            # Rule 3: Clean up work directory after 30 days
            s3.BucketLifecycleConfigurationV2RuleArgs(
                id="cleanup-work-directory",
                status="Enabled",
                filter=s3.BucketLifecycleConfigurationV2RuleFilterArgs(prefix="work/"),
                expiration=s3.BucketLifecycleConfigurationV2RuleExpirationArgs(days=30),
            ),
            # Rule 4: Clean up scratch directory after 30 days
            s3.BucketLifecycleConfigurationV2RuleArgs(
                id="cleanup-scratch-directory",
                status="Enabled",
                filter=s3.BucketLifecycleConfigurationV2RuleFilterArgs(
                    prefix="scratch/"
                ),
                expiration=s3.BucketLifecycleConfigurationV2RuleExpirationArgs(days=30),
            ),
            # Rule 5: Clean up cache directories after 30 days
            s3.BucketLifecycleConfigurationV2RuleArgs(
                id="cleanup-cache-directories",
                status="Enabled",
                filter=s3.BucketLifecycleConfigurationV2RuleFilterArgs(prefix="cache/"),
                expiration=s3.BucketLifecycleConfigurationV2RuleExpirationArgs(days=30),
            ),
            # Rule 6: Clean up .cache directories after 30 days
            s3.BucketLifecycleConfigurationV2RuleArgs(
                id="cleanup-dot-cache-directories",
                status="Enabled",
                filter=s3.BucketLifecycleConfigurationV2RuleFilterArgs(
                    prefix=".cache/"
                ),
                expiration=s3.BucketLifecycleConfigurationV2RuleExpirationArgs(days=30),
            ),
            # Rule 7: Clean up incomplete multipart uploads
            s3.BucketLifecycleConfigurationV2RuleArgs(
                id="cleanup-incomplete-multipart-uploads",
                status="Enabled",
                abort_incomplete_multipart_upload=s3.BucketLifecycleConfigurationV2RuleAbortIncompleteMultipartUploadArgs(
                    days_after_initiation=7
                ),
            ),
        ],
        opts=pulumi.ResourceOptions(provider=aws_provider, depends_on=[bucket]),
    )

    return lifecycle_configuration


def create_s3_cors_configuration(aws_provider, bucket):
    """Create S3 CORS configuration for Seqera Data Explorer compatibility.

    Args:
        aws_provider: Configured AWS provider instance
        bucket: S3 bucket resource

    Returns:
        S3 bucket CORS configuration resource
    """
    # S3 CORS configuration for Seqera Data Explorer compatibility
    # Based on official Seqera documentation:
    # https://docs.seqera.io/platform-cloud/data/data-explorer#amazon-s3-cors-configuration
    cors_configuration = s3.BucketCorsConfigurationV2(
        "nf-core-awsmegatests-cors",
        bucket=bucket.id,
        cors_rules=[
            s3.BucketCorsConfigurationV2CorsRuleArgs(
                id="SeqeraDataExplorerAccess",
                allowed_headers=["*"],
                allowed_methods=["GET", "HEAD", "POST", "PUT", "DELETE"],
                allowed_origins=[
                    "https://*.cloud.seqera.io",
                    "https://*.tower.nf",
                    "https://cloud.seqera.io",
                    "https://tower.nf",
                ],
                expose_headers=["ETag"],
                max_age_seconds=3000,
            ),
            # Additional rule for direct browser access
            s3.BucketCorsConfigurationV2CorsRuleArgs(
                id="BrowserDirectAccess",
                allowed_headers=["Authorization", "Content-Type", "Range"],
                allowed_methods=["GET", "HEAD"],
                allowed_origins=["*"],
                expose_headers=["Content-Range", "Content-Length", "ETag"],
                max_age_seconds=3000,
            ),
        ],
        opts=pulumi.ResourceOptions(provider=aws_provider, depends_on=[bucket]),
    )

    return cors_configuration
