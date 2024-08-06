"""An AWS Python Pulumi program"""

import json
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
    opts=pulumi.ResourceOptions(protect=True),
)

# Step 2: Create a bucket policy for public read access
public_read_policy = json.dumps(
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": "*",  # Allow access to anyone
                "Action": [
                    "s3:GetObject",
                    "s3:ListBucket",
                ],
                "Resource": [
                    test_datasets_bucket.arn.apply(lambda arn: f"{arn}/*"),
                ],  # Access all objects in the bucket
            }
        ],
    }
)

# Step 3: Apply the bucket policy to the bucket
bucket_policy = aws.s3.BucketPolicy(
    "testData-bucketPolicy", bucket=test_datasets_bucket.id, policy=public_read_policy
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

# Export the bucket name
pulumi.export("bucket_name", test_datasets_bucket.bucket)  # type: ignore[attr-defined]
