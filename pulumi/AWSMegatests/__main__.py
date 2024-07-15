"""An AWS Python Pulumi program"""

import pulumi
import pulumi_aws as aws

awsmegatests_bucket = aws.s3.Bucket(
    "awsmegatests-bucket",
    arn="arn:aws:s3:::nf-core-awsmegatests",
    bucket="nf-core-awsmegatests",
    cors_rules=[
        aws.s3.BucketCorsRuleArgs(
            allowed_headers=["*"],
            allowed_methods=[
                "HEAD",
                "GET",
            ],
            allowed_origins=[
                "https://s3.amazonaws.com",
                "https://s3-eu-west-1.amazonaws.com",
                "https://s3.eu-west-1.amazonaws.com",
                "*",
            ],
            expose_headers=[
                "ETag",
                "x-amz-meta-custom-header",
            ],
            max_age_seconds=0,
        )
    ],
    hosted_zone_id="Z1BKCTXD74EZPE",
    lifecycle_rules=[
        aws.s3.BucketLifecycleRuleArgs(
            abort_incomplete_multipart_upload_days=0,
            enabled=True,
            expiration=aws.s3.BucketLifecycleRuleExpirationArgs(
                date="",
                days=10,
                expired_object_delete_marker=False,
            ),
            id="Delete_files_older_than_10_days_in_work_directory",
            noncurrent_version_transitions=[],
            prefix="work",
            tags={},
            transitions=[],
        ),
        aws.s3.BucketLifecycleRuleArgs(
            abort_incomplete_multipart_upload_days=0,
            enabled=True,
            expiration=aws.s3.BucketLifecycleRuleExpirationArgs(
                date="",
                days=10,
                expired_object_delete_marker=False,
            ),
            id="Delete files older than 10 days in _nextflow folder",
            noncurrent_version_transitions=[],
            prefix="_nextflow",
            tags={},
            transitions=[],
        ),
        aws.s3.BucketLifecycleRuleArgs(
            abort_incomplete_multipart_upload_days=0,
            enabled=True,
            expiration=aws.s3.BucketLifecycleRuleExpirationArgs(
                date="",
                days=10,
                expired_object_delete_marker=False,
            ),
            id="Delete files older than 10 days in scratch directory",
            noncurrent_version_expiration=aws.s3.BucketLifecycleRuleNoncurrentVersionExpirationArgs(
                days=1,
            ),
            noncurrent_version_transitions=[],
            prefix="scratch",
            tags={},
            transitions=[],
        ),
        aws.s3.BucketLifecycleRuleArgs(
            abort_incomplete_multipart_upload_days=0,
            enabled=True,
            id="Move_to_intelligent_tier_after_11_days",
            noncurrent_version_transitions=[],
            prefix="",
            tags={},
            transitions=[
                aws.s3.BucketLifecycleRuleTransitionArgs(
                    date="",
                    days=11,
                    storage_class="INTELLIGENT_TIERING",
                )
            ],
        ),
    ],
    request_payer="BucketOwner",
    server_side_encryption_configuration=aws.s3.BucketServerSideEncryptionConfigurationArgs(
        rule=aws.s3.BucketServerSideEncryptionConfigurationRuleArgs(
            apply_server_side_encryption_by_default=aws.s3.BucketServerSideEncryptionConfigurationRuleApplyServerSideEncryptionByDefaultArgs(
                sse_algorithm="AES256",
            ),
        ),
    ),
    opts=pulumi.ResourceOptions(protect=True),
)

# awsmegatests_bucket_acl = aws.s3.BucketAclV2(
#     "awsmegatests-bucket-acl",
#     access_control_policy=aws.s3.BucketAclV2AccessControlPolicyArgs(
#         grants=[
#             aws.s3.BucketAclV2AccessControlPolicyGrantArgs(
#                 grantee=aws.s3.BucketAclV2AccessControlPolicyGrantGranteeArgs(
#                     display_name="phil.ewels",
#                     email_address="",
#                     id="f1ab567ea0ccaf20e2165c9a69391bc9e0ad0517fb77cb733a54b37401b9aa74",
#                     type="CanonicalUser",
#                     uri="",
#                 ),
#                 permission="FULL_CONTROL",
#             )
#         ],
#         owner=aws.s3.BucketAclV2AccessControlPolicyOwnerArgs(
#             display_name="phil.ewels",
#             id="f1ab567ea0ccaf20e2165c9a69391bc9e0ad0517fb77cb733a54b37401b9aa74",
#         ),
#     ),
#     bucket="nf-core-awsmegatests",
#     opts=pulumi.ResourceOptions(protect=True),
# )

# import pulumi_aws_native as aws_native

# awsmegatests_bucket_native = aws_native.s3.Bucket(
#     "awsmegatests-bucket-native",
#     analytics_configurations=[
#         aws_native.s3.BucketAnalyticsConfigurationArgs(
#             id="storage_class-0.1",
#             storage_class_analysis=aws_native.s3.BucketStorageClassAnalysisArgs(),
#         )
#     ],
#     bucket_encryption=aws_native.s3.BucketEncryptionArgs(
#         server_side_encryption_configuration=[
#             aws_native.s3.BucketServerSideEncryptionRuleArgs(
#                 bucket_key_enabled=False,
#                 server_side_encryption_by_default=aws_native.s3.BucketServerSideEncryptionByDefaultArgs(
#                     sse_algorithm=aws_native.s3.BucketServerSideEncryptionByDefaultSseAlgorithm.AES256,
#                 ),
#             )
#         ],
#     ),
#     bucket_name="nf-core-awsmegatests",
#     cors_configuration=aws_native.s3.BucketCorsConfigurationArgs(
#         cors_rules=[
#             aws_native.s3.BucketCorsRuleArgs(
#                 allowed_headers=["*"],
#                 allowed_methods=[
#                     aws_native.s3.BucketCorsRuleAllowedMethodsItem.HEAD,
#                     aws_native.s3.BucketCorsRuleAllowedMethodsItem.GET,
#                 ],
#                 allowed_origins=[
#                     "https://s3.amazonaws.com",
#                     "https://s3-eu-west-1.amazonaws.com",
#                     "https://s3.eu-west-1.amazonaws.com",
#                     "*",
#                 ],
#                 exposed_headers=[
#                     "ETag",
#                     "x-amz-meta-custom-header",
#                 ],
#             )
#         ],
#     ),
#     lifecycle_configuration=aws_native.s3.BucketLifecycleConfigurationArgs(
#         rules=[
#             aws_native.s3.BucketRuleArgs(
#                 expiration_in_days=10,
#                 id="Delete_files_older_than_10_days_in_work_directory",
#                 prefix="work",
#                 status=aws_native.s3.BucketRuleStatus.ENABLED,
#             ),
#             aws_native.s3.BucketRuleArgs(
#                 expiration_in_days=10,
#                 id="Delete files older than 10 days in _nextflow folder",
#                 prefix="_nextflow",
#                 status=aws_native.s3.BucketRuleStatus.ENABLED,
#             ),
#             aws_native.s3.BucketRuleArgs(
#                 expiration_in_days=10,
#                 id="Delete files older than 10 days in scratch directory",
#                 noncurrent_version_expiration=aws_native.s3.BucketNoncurrentVersionExpirationArgs(
#                     noncurrent_days=1,
#                 ),
#                 prefix="scratch",
#                 status=aws_native.s3.BucketRuleStatus.ENABLED,
#             ),
#             aws_native.s3.BucketRuleArgs(
#                 id="Move_to_intelligent_tier_after_11_days",
#                 status=aws_native.s3.BucketRuleStatus.ENABLED,
#                 transitions=[
#                     aws_native.s3.BucketTransitionArgs(
#                         storage_class=aws_native.s3.BucketTransitionStorageClass.INTELLIGENT_TIERING,
#                         transition_in_days=11,
#                     )
#                 ],
#             ),
#         ],
#     ),
#     metrics_configurations=[
#         aws_native.s3.BucketMetricsConfigurationArgs(
#             id="all-objects",
#         )
#     ],
#     public_access_block_configuration=aws_native.s3.BucketPublicAccessBlockConfigurationArgs(
#         block_public_acls=False,
#         block_public_policy=False,
#         ignore_public_acls=False,
#         restrict_public_buckets=False,
#     ),
#     opts=pulumi.ResourceOptions(protect=True),
# )
