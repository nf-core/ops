"""An AWS Python Pulumi program"""

import pulumi
import pulumi_aws as aws
import pulumi_github as github
# Uncomment this line after installing the 1Password provider
import pulumi_onepassword as onepassword

# Configure the 1Password provider explicitly
onepassword_config = pulumi.Config("pulumi-onepassword")
onepassword_provider = onepassword.Provider("onepassword-provider",
    service_account_token=onepassword_config.require_secret("service_account_token")
)

# Get GitHub token from 1Password using the get_item function
github_token_item = onepassword.get_item_output(
    vault="Dev",
    title="GitHub nf-core PA Token Pulumi",
    opts=pulumi.InvokeOptions(provider=onepassword_provider)
)

# For now, let's use Pulumi config for AWS credentials
# You can set them with:
# pulumi config set aws:accessKey <your-access-key> --secret
# pulumi config set aws:secretKey <your-secret-key> --secret

# Use the default AWS provider which will read from Pulumi config
# The region is already set via: pulumi config set aws:region eu-north-1
aws_provider = aws.Provider("aws-provider")

# Configure GitHub provider using token from 1Password
github_provider = github.Provider("github-provider",
    token=github_token_item.credential,
    owner="nf-core"  # Set the GitHub organization
)

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
    opts=pulumi.ResourceOptions(provider=aws_provider)  
)

test_datasets_bucket_publicaccessblock = aws.s3.BucketPublicAccessBlock(
    "test-datasets-bucket-publicaccessblock",
    bucket="nf-core-test-datasets",
    opts=pulumi.ResourceOptions(protect=True, provider=aws_provider)  
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
    opts=pulumi.ResourceOptions(provider=aws_provider)
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
    opts=pulumi.ResourceOptions(provider=aws_provider)
)

# List of AWS user names to attach the policy to
usernames = ["edmund", "maxime"]

# Attach the policy to each user
for username in usernames:
    aws.iam.UserPolicyAttachment(
        f"{username}-putPolicyAttachment", 
        user=username, 
        policy_arn=policy.arn,
        opts=pulumi.ResourceOptions(provider=aws_provider)
    )

# For now, keep the IAM user creation for CI/CD, but we'll manage it through 1Password later
# This is more secure than hardcoded credentials

# Create a dedicated IAM user for CI/CD access to this bucket
ci_user = aws.iam.User(
    "test-datasets-ci-user",
    name="nf-core-test-datasets-ci",
    path="/",
    opts=pulumi.ResourceOptions(provider=aws_provider)
)

# Create access keys for the CI user
ci_user_access_key = aws.iam.AccessKey(
    "test-datasets-ci-access-key",
    user=ci_user.name,
    opts=pulumi.ResourceOptions(provider=aws_provider)
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
    # opts=pulumi.ResourceOptions(provider=aws_provider)  # Uncomment when using 1Password
)

# Attach the comprehensive policy to the CI user
aws.iam.UserPolicyAttachment(
    "ci-user-bucket-policy-attachment",
    user=ci_user.name,
    policy_arn=bucket_access_policy.arn,
    # opts=pulumi.ResourceOptions(provider=aws_provider)  # Uncomment when using 1Password
)

# Create GitHub Actions secrets for the AWS credentials
# This replaces the functionality from add_github_secrets.py

# AWS Access Key ID secret
aws_access_key_secret = github.ActionsSecret(
    "aws-access-key-id-secret",
    repository="ops",  # Repository name (not full name)
    secret_name="AWS_ACCESS_KEY_ID",
    plaintext_value=ci_user_access_key.id,
    opts=pulumi.ResourceOptions(provider=github_provider)
)

# AWS Secret Access Key secret
aws_secret_access_key_secret = github.ActionsSecret(
    "aws-secret-access-key-secret",
    repository="ops",  # Repository name (not full name)
    secret_name="AWS_SECRET_ACCESS_KEY",
    plaintext_value=ci_user_access_key.secret,
    opts=pulumi.ResourceOptions(provider=github_provider)
)

# AWS Region secret
aws_region_secret = github.ActionsSecret(
    "aws-region-secret",
    repository="ops",  # Repository name (not full name)
    secret_name="AWS_REGION",
    plaintext_value="eu-north-1",  # Based on your CORS configuration
    opts=pulumi.ResourceOptions(provider=github_provider)
)

# Export the bucket name
pulumi.export("bucket_name", test_datasets_bucket.bucket)  # type: ignore[attr-defined]

# Export the CI user credentials (these will be stored in 1Password)
pulumi.export("ci_user_access_key_id", ci_user_access_key.id)
pulumi.export("ci_user_secret_access_key", pulumi.Output.secret(ci_user_access_key.secret))
pulumi.export("ci_user_name", ci_user.name)

# Export GitHub secrets information
pulumi.export("github_secrets_created", {
    "AWS_ACCESS_KEY_ID": aws_access_key_secret.secret_name,
    "AWS_SECRET_ACCESS_KEY": aws_secret_access_key_secret.secret_name,
    "AWS_REGION": aws_region_secret.secret_name
})