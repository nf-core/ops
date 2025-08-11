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
    bucket_lifecycle_configuration = None

    return {
        "bucket": nf_core_awsmegatests_bucket,
        "lifecycle_configuration": bucket_lifecycle_configuration,
    }


# uv run pulumi import aws:s3/bucket:Bucket nf-core-awsmegatests nf-core-awsmegatests
# nf_core_awsmegatests = aws.s3.Bucket("nf-core-awsmegatests",
#     arn="arn:aws:s3:::nf-core-awsmegatests",
#     bucket="nf-core-awsmegatests",
#     cors_rules=[{
#         "allowed_headers": ["*"],
#         "allowed_methods": [
#             "HEAD",
#             "GET",
#         ],
#         "allowed_origins": [
#             "https://s3.amazonaws.com",
#             "https://s3-eu-west-1.amazonaws.com",
#             "https://s3.eu-west-1.amazonaws.com",
#             "*",
#         ],
#         "expose_headers": [
#             "ETag",
#             "x-amz-meta-custom-header",
#         ],
#     }],
#     hosted_zone_id="Z1BKCTXD74EZPE",
#     lifecycle_rules=[
#         {
#             "enabled": True,
#             "id": "preserve-metadata-files",
#             "tags": {
#                 "nextflow.io/metadata": "true",
#             },
#             "transitions": [
#                 {
#                     "days": 30,
#                     "storage_class": "STANDARD_IA",
#                 },
#                 {
#                     "days": 90,
#                     "storage_class": "GLACIER",
#                 },
#             ],
#         },
#         {
#             "enabled": True,
#             "expiration": {
#                 "days": 30,
#             },
#             "id": "cleanup-temporary-files",
#             "tags": {
#                 "nextflow.io/temporary": "true",
#             },
#         },
#         {
#             "enabled": True,
#             "expiration": {
#                 "days": 90,
#             },
#             "id": "cleanup-work-directory",
#             "prefix": "work/",
#         },
#         {
#             "abort_incomplete_multipart_upload_days": 7,
#             "enabled": True,
#             "id": "cleanup-incomplete-multipart-uploads",
#         },
#     ],
#     request_payer="BucketOwner",
#     server_side_encryption_configuration={
#         "rule": {
#             "apply_server_side_encryption_by_default": {
#                 "sse_algorithm": "AES256",
#             },
#         },
#     },
#     opts = pulumi.ResourceOptions(protect=True))
