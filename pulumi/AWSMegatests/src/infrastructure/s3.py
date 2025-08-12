"""S3 infrastructure management for AWS Megatests."""

from typing import Dict, Any

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
    # Create lifecycle rules for automated cost optimization and cleanup
    try:
        bucket_lifecycle_configuration = create_s3_lifecycle_configuration(
            aws_provider, nf_core_awsmegatests_bucket
        )
        pulumi.log.info("S3 lifecycle configuration created successfully")
    except Exception as e:
        # Fall back to manual management if permissions are insufficient
        pulumi.log.warn(f"S3 lifecycle configuration failed, managing manually: {e}")
        bucket_lifecycle_configuration = None

    return {
        "bucket": nf_core_awsmegatests_bucket,
        "lifecycle_configuration": bucket_lifecycle_configuration,
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
            # Rule 3: Clean up work directory after 90 days
            s3.BucketLifecycleConfigurationV2RuleArgs(
                id="cleanup-work-directory",
                status="Enabled",
                filter=s3.BucketLifecycleConfigurationV2RuleFilterArgs(prefix="work/"),
                expiration=s3.BucketLifecycleConfigurationV2RuleExpirationArgs(days=90),
            ),
            # Rule 4: Clean up incomplete multipart uploads
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
