"""CO2 Reports S3 Infrastructure Management

A Pulumi program for managing the nf-core CO2 footprint reports S3 bucket.

This project creates and manages AWS infrastructure for storing CO2 footprint
tracking data from nf-test runs in the nf-core/modules repository.
"""

import pulumi
import pulumi_aws as aws
import pulumi_github as github
import pulumi_onepassword as onepassword

# Configure the 1Password provider
onepassword_config = pulumi.Config("pulumi-onepassword")
onepassword_provider = onepassword.Provider(
    "onepassword-provider",
    service_account_token=onepassword_config.require_secret("service_account_token"),
    account="",  # Explicitly disable CLI account detection to avoid conflicts
)

# Get GitHub token from 1Password
github_token_item = onepassword.get_item_output(
    vault="Dev",
    title="GitHub nf-core PA Token Pulumi",
    opts=pulumi.InvokeOptions(provider=onepassword_provider),
)

# Configure AWS provider
aws_provider = aws.Provider("aws-provider")

# Configure GitHub provider
github_provider = github.Provider(
    "github-provider",
    token=github_token_item.credential,
    owner=pulumi.Config("github").get("owner"),
)

# Create S3 bucket for CO2 reports
co2_reports_bucket = aws.s3.Bucket(
    "co2-reports-bucket",
    bucket="nf-core-co2-reports",
    opts=pulumi.ResourceOptions(provider=aws_provider),
)

# Configure server-side encryption for the bucket
co2_reports_bucket_encryption = aws.s3.BucketServerSideEncryptionConfigurationV2(
    "co2-reports-bucket-encryption",
    bucket=co2_reports_bucket.id,
    rules=[
        aws.s3.BucketServerSideEncryptionConfigurationV2RuleArgs(
            apply_server_side_encryption_by_default=aws.s3.BucketServerSideEncryptionConfigurationV2RuleApplyServerSideEncryptionByDefaultArgs(
                sse_algorithm="AES256",
            ),
        ),
    ],
    opts=pulumi.ResourceOptions(provider=aws_provider),
)

# Enable versioning for the bucket
co2_reports_bucket_versioning = aws.s3.BucketVersioningV2(
    "co2-reports-bucket-versioning",
    bucket=co2_reports_bucket.id,
    versioning_configuration=aws.s3.BucketVersioningV2VersioningConfigurationArgs(
        status="Enabled",
    ),
    opts=pulumi.ResourceOptions(provider=aws_provider),
)

# Block public access to the bucket
co2_reports_bucket_public_access_block = aws.s3.BucketPublicAccessBlock(
    "co2-reports-bucket-public-access-block",
    bucket=co2_reports_bucket.id,
    block_public_acls=True,
    block_public_policy=True,
    ignore_public_acls=True,
    restrict_public_buckets=True,
    opts=pulumi.ResourceOptions(provider=aws_provider),
)

# Create IAM user for CI/CD
ci_user = aws.iam.User(
    "co2-reports-ci-user",
    name="nf-core-co2-reports-ci",
    path="/",
    opts=pulumi.ResourceOptions(provider=aws_provider),
)

# Create access keys for the CI user
ci_user_access_key = aws.iam.AccessKey(
    "co2-reports-ci-access-key",
    user=ci_user.name,
    opts=pulumi.ResourceOptions(provider=aws_provider),
)

# Create IAM policy for bucket access
bucket_access_policy = aws.iam.Policy(
    "co2-reports-bucket-access-policy",
    name="nf-core-co2-reports-bucket-access",
    description="Write access to nf-core-co2-reports S3 bucket for CI/CD",
    policy=co2_reports_bucket.arn.apply(
        lambda bucket_arn: f"""{{
      "Version": "2012-10-17",
      "Statement": [
        {{
          "Effect": "Allow",
          "Action": [
            "s3:PutObject",
            "s3:PutObjectAcl",
            "s3:GetObject",
            "s3:ListBucket",
            "s3:GetBucketLocation"
          ],
          "Resource": [
            "{bucket_arn}",
            "{bucket_arn}/*"
          ]
        }}
      ]
    }}"""
    ),
    opts=pulumi.ResourceOptions(provider=aws_provider),
)

# Attach policy to CI user
aws.iam.UserPolicyAttachment(
    "ci-user-bucket-policy-attachment",
    user=ci_user.name,
    policy_arn=bucket_access_policy.arn,
    opts=pulumi.ResourceOptions(provider=aws_provider),
)

# Create GitHub Actions secrets for the modules repository
aws_access_key_secret = github.ActionsSecret(
    "co2-reports-aws-access-key-id-secret",
    repository="modules",
    secret_name="CO2_REPORTS_AWS_ACCESS_KEY_ID",
    plaintext_value=ci_user_access_key.id,
    opts=pulumi.ResourceOptions(provider=github_provider),
)

aws_secret_access_key_secret = github.ActionsSecret(
    "co2-reports-aws-secret-access-key-secret",
    repository="modules",
    secret_name="CO2_REPORTS_AWS_SECRET_ACCESS_KEY",
    plaintext_value=ci_user_access_key.secret,
    opts=pulumi.ResourceOptions(provider=github_provider),
)

aws_region_secret = github.ActionsSecret(
    "co2-reports-aws-region-secret",
    repository="modules",
    secret_name="CO2_REPORTS_AWS_REGION",
    plaintext_value=pulumi.Config("aws").get("region") or "us-east-1",
    opts=pulumi.ResourceOptions(provider=github_provider),
)

# Exports
pulumi.export("bucket_name", co2_reports_bucket.bucket)
pulumi.export("bucket_arn", co2_reports_bucket.arn)
pulumi.export("ci_user_name", ci_user.name)
pulumi.export("ci_user_access_key_id", ci_user_access_key.id)
pulumi.export(
    "ci_user_secret_access_key", pulumi.Output.secret(ci_user_access_key.secret)
)
pulumi.export(
    "github_secrets_created",
    {
        "CO2_REPORTS_AWS_ACCESS_KEY_ID": aws_access_key_secret.secret_name,
        "CO2_REPORTS_AWS_SECRET_ACCESS_KEY": aws_secret_access_key_secret.secret_name,
        "CO2_REPORTS_AWS_REGION": aws_region_secret.secret_name,
    },
)
pulumi.export(
    "usage",
    {
        "s3_uri": "s3://nf-core-co2-reports/",
        "upload_path_pattern": "s3://nf-core-co2-reports/modules/YYYY-MM-DD/branch-name/profile/shard/",
    },
)
