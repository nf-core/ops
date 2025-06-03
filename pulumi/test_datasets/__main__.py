"""An AWS Python Pulumi program"""

import pulumi
import pulumi_aws as aws

test_datasets_bucket = aws.s3.Bucket(
    "test-datasets-bucket",
    arn="arn:aws:s3:::nf-core-test-datasets",
    bucket="nf-core-test-datasets",
    acl="public-read",
    cors_rules=[
        aws.s3.BucketCorsRuleArgs(
            allowed_headers=["*"],
            allowed_methods=[
                "HEAD",
                "GET",
            ],
            allowed_origins=[
                "https://s3.amazonaws.com",
                "https://s3-eu-north-1.amazonaws.com",
                "https://s3.eu-north-1.amazonaws.com",
                "*",
            ],
            expose_headers=[
                "ETag",
                "x-amz-meta-custom-header",
            ],
            max_age_seconds=0,
        )
    ],
    request_payer="BucketOwner",
    server_side_encryption_configuration=aws.s3.BucketServerSideEncryptionConfigurationArgs(
        rule=aws.s3.BucketServerSideEncryptionConfigurationRuleArgs(
            apply_server_side_encryption_by_default=aws.s3.BucketServerSideEncryptionConfigurationRuleApplyServerSideEncryptionByDefaultArgs(
                sse_algorithm="AES256",
            ),
        ),
    ),
)

test_datasets_bucket_publicaccessblock = aws.s3.BucketPublicAccessBlock(
    "test-datasets-bucket-publicaccessblock",
    bucket="nf-core-test-datasets",
    opts=pulumi.ResourceOptions(protect=True),  # type: ignore[attr-defined]
)

allow_access_from_anyone = aws.iam.get_policy_document_output(
    statements=[
        {
            "principals": [{"identifiers": ["*"], "type": "AWS"}],
            "actions": [
                "s3:GetObject",
                "s3:ListBucket",
            ],
            "resources": [
                test_datasets_bucket.arn,
                test_datasets_bucket.arn.apply(lambda arn: f"{arn}/*"),
            ],
        }
    ]
)

allow_access_from_anyone_bucket_policy = aws.s3.BucketPolicy(
    "allow_access_from_anyone",
    bucket=test_datasets_bucket.id,
    policy=allow_access_from_anyone.json,
)

# Define the policy which allows users to put objects in the S3 bucket
policy = aws.iam.Policy(
    "bucketPutPolicy",
    description="Allow users to put objects in the S3 bucket",
    policy=test_datasets_bucket.arn.apply(
        lambda bucket_arn: f"""{{
      "Version": "2012-10-17",
      "Statement": [
        {{
          "Effect": "Allow",
          "Action": "s3:PutObject",
          "Resource": "{bucket_arn}/*"
        }}
      ]
    }}"""
    ),
)

# List of AWS user names to attach the policy to
usernames = ["edmund", "maxime"]

# Attach the policy to each user
for username in usernames:
    aws.iam.UserPolicyAttachment(
        f"{username}-putPolicyAttachment", user=username, policy_arn=policy.arn
    )

# Create a dedicated IAM user for CI/CD access to this bucket
ci_user = aws.iam.User(
    "test-datasets-ci-user",
    name="nf-core-test-datasets-ci",
    path="/",
)

# Create access keys for the CI user
ci_user_access_key = aws.iam.AccessKey(
    "test-datasets-ci-access-key",
    user=ci_user.name,
)

# Create a comprehensive policy for full bucket access
bucket_access_policy = aws.iam.Policy(
    "test-datasets-bucket-access-policy",
    name="nf-core-test-datasets-bucket-access",
    description="Full access to nf-core-test-datasets S3 bucket",
    policy=test_datasets_bucket.arn.apply(
        lambda bucket_arn: f"""{{
      "Version": "2012-10-17",
      "Statement": [
        {{
          "Effect": "Allow",
          "Action": [
            "s3:GetObject",
            "s3:GetObjectVersion",
            "s3:PutObject",
            "s3:PutObjectAcl",
            "s3:DeleteObject",
            "s3:DeleteObjectVersion",
            "s3:ListBucket",
            "s3:ListBucketVersions",
            "s3:GetBucketLocation",
            "s3:GetBucketVersioning"
          ],
          "Resource": [
            "{bucket_arn}",
            "{bucket_arn}/*"
          ]
        }}
      ]
    }}"""
    ),
)

# Attach the comprehensive policy to the CI user
aws.iam.UserPolicyAttachment(
    "ci-user-bucket-policy-attachment",
    user=ci_user.name,
    policy_arn=bucket_access_policy.arn,
)

# Export the bucket name
pulumi.export("bucket_name", test_datasets_bucket.bucket)  # type: ignore[attr-defined]
# Export the CI user credentials (mark as secret)
pulumi.export("ci_user_access_key_id", ci_user_access_key.id)
pulumi.export("ci_user_secret_access_key", pulumi.Output.secret(ci_user_access_key.secret))
pulumi.export("ci_user_name", ci_user.name)
