"""S3 infrastructure management for AWS Megatests"""

import pulumi
from pulumi_aws import s3


def create_s3_infrastructure(aws_provider):
    """Create S3 bucket and lifecycle configuration"""

    # Import existing AWS resources used by nf-core megatests
    # S3 bucket for Nextflow work directory (already exists)
    nf_core_awsmegatests_bucket = s3.Bucket(
        "nf-core-awsmegatests",
        bucket="nf-core-awsmegatests",
        opts=pulumi.ResourceOptions(
            import_="nf-core-awsmegatests",  # Import existing bucket
            protect=True,  # Protect from accidental deletion
            provider=aws_provider,  # Use configured AWS provider
            ignore_changes=[
                "cors_rules",
                "lifecycle_rules",
                "versioning",
            ],  # Don't modify existing configurations
        ),
    )

    # S3 bucket lifecycle configuration for metadata preservation and temporary file cleanup
    bucket_lifecycle_configuration = s3.BucketLifecycleConfigurationV2(
        "nf-core-awsmegatests-lifecycle",
        bucket=nf_core_awsmegatests_bucket.id,
        rules=[
            # Rule 1: Preserve metadata files indefinitely (tagged with nextflow.io/metadata=true)
            s3.BucketLifecycleConfigurationV2RuleArgs(
                id="preserve-metadata-files",
                status="Enabled",
                filter=s3.BucketLifecycleConfigurationV2RuleFilterArgs(
                    tag=s3.BucketLifecycleConfigurationV2RuleFilterTagArgs(
                        key="nextflow.io/metadata", value="true"
                    )
                ),
                transitions=[
                    # Transition metadata files to IA after 30 days for cost savings
                    s3.BucketLifecycleConfigurationV2RuleTransitionArgs(
                        days=30, storage_class="STANDARD_IA"
                    ),
                    # Transition to Glacier after 90 days for long-term preservation
                    s3.BucketLifecycleConfigurationV2RuleTransitionArgs(
                        days=90, storage_class="GLACIER"
                    ),
                ],
                # No expiration for metadata files - preserve indefinitely
            ),
            # Rule 2: Clean up temporary files (tagged with nextflow.io/temporary=true)
            s3.BucketLifecycleConfigurationV2RuleArgs(
                id="cleanup-temporary-files",
                status="Enabled",
                filter=s3.BucketLifecycleConfigurationV2RuleFilterArgs(
                    tag=s3.BucketLifecycleConfigurationV2RuleFilterTagArgs(
                        key="nextflow.io/temporary", value="true"
                    )
                ),
                expiration=s3.BucketLifecycleConfigurationV2RuleExpirationArgs(
                    days=30  # Delete temporary files after 30 days
                ),
            ),
            # Rule 3: Default cleanup for work directory files without tags
            s3.BucketLifecycleConfigurationV2RuleArgs(
                id="cleanup-work-directory",
                status="Enabled",
                filter=s3.BucketLifecycleConfigurationV2RuleFilterArgs(
                    prefix="work/"  # Apply to work directory
                ),
                expiration=s3.BucketLifecycleConfigurationV2RuleExpirationArgs(
                    days=90  # Delete untagged work files after 90 days
                ),
            ),
            # Rule 4: Cleanup for incomplete multipart uploads
            s3.BucketLifecycleConfigurationV2RuleArgs(
                id="cleanup-incomplete-multipart-uploads",
                status="Enabled",
                abort_incomplete_multipart_upload=s3.BucketLifecycleConfigurationV2RuleAbortIncompleteMultipartUploadArgs(
                    days_after_initiation=7
                ),
            ),
        ],
        opts=pulumi.ResourceOptions(
            provider=aws_provider, depends_on=[nf_core_awsmegatests_bucket]
        ),
    )

    return {
        "bucket": nf_core_awsmegatests_bucket,
        "lifecycle_configuration": bucket_lifecycle_configuration,
    }
