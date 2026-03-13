"""Bootstrap Pulumi project to create S3 bucket for Pulumi state storage.

This project uses a local backend to avoid circular dependency.
All other Pulumi projects will use the S3 bucket created here.
"""

import pulumi
import pulumi_aws as aws

# Configuration
BUCKET_NAME = "nf-core-pulumi-state"
REGION = "eu-north-1"

# Create S3 bucket for Pulumi state storage
state_bucket = aws.s3.Bucket(
    "pulumi-state-bucket",
    bucket=BUCKET_NAME,
    # Force destroy for cleanup (remove in production if needed)
    force_destroy=False,
    tags={
        "Name": BUCKET_NAME,
        "project": "pulumi-state",
        "managed-by": "pulumi",
        "environment": "shared",
        "purpose": "pulumi-state-storage",
    },
)

# Enable versioning for state history
versioning = aws.s3.BucketVersioningV2(
    "state-bucket-versioning",
    bucket=state_bucket.id,
    versioning_configuration=aws.s3.BucketVersioningV2VersioningConfigurationArgs(
        status="Enabled",
    ),
)

# Enable server-side encryption
encryption = aws.s3.BucketServerSideEncryptionConfigurationV2(
    "state-bucket-encryption",
    bucket=state_bucket.id,
    rules=[
        aws.s3.BucketServerSideEncryptionConfigurationV2RuleArgs(
            apply_server_side_encryption_by_default=aws.s3.BucketServerSideEncryptionConfigurationV2RuleApplyServerSideEncryptionByDefaultArgs(
                sse_algorithm="AES256",
            ),
            bucket_key_enabled=True,
        )
    ],
)

# Block all public access
public_access_block = aws.s3.BucketPublicAccessBlock(
    "state-bucket-public-access-block",
    bucket=state_bucket.id,
    block_public_acls=True,
    block_public_policy=True,
    ignore_public_acls=True,
    restrict_public_buckets=True,
)

# Lifecycle policy to clean up old versions
lifecycle_configuration = aws.s3.BucketLifecycleConfigurationV2(
    "state-bucket-lifecycle",
    bucket=state_bucket.id,
    rules=[
        aws.s3.BucketLifecycleConfigurationV2RuleArgs(
            id="expire-old-versions",
            status="Enabled",
            noncurrent_version_expiration=aws.s3.BucketLifecycleConfigurationV2RuleNoncurrentVersionExpirationArgs(
                noncurrent_days=90,
            ),
        ),
        aws.s3.BucketLifecycleConfigurationV2RuleArgs(
            id="abort-incomplete-multipart-uploads",
            status="Enabled",
            abort_incomplete_multipart_upload=aws.s3.BucketLifecycleConfigurationV2RuleAbortIncompleteMultipartUploadArgs(
                days_after_initiation=7,
            ),
        ),
    ],
)

# Exports
pulumi.export("bucket_name", state_bucket.bucket)
pulumi.export("bucket_arn", state_bucket.arn)
pulumi.export("bucket_region", REGION)
pulumi.export(
    "usage_instructions",
    pulumi.Output.concat(
        "To use this bucket as your Pulumi backend:\n",
        "  pulumi login s3://",
        state_bucket.bucket,
        "\n\n",
        "Or with explicit region:\n",
        "  pulumi login 's3://",
        state_bucket.bucket,
        f"?region={REGION}&awssdk=v2'",
    ),
)
