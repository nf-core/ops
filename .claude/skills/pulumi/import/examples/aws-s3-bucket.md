# Importing AWS S3 Buckets

Complete walkthrough for importing existing S3 buckets and related configurations into Pulumi.

## Scenario: Import nf-core-co2-reports Bucket

### Background

The `nf-core-co2-reports` bucket was created manually via AWS Console for CO2 footprint tracking. We want to bring it under Pulumi management.

**Bucket details:**

- Name: `nf-core-co2-reports`
- Region: `eu-north-1`
- Features: Versioning enabled, encryption enabled, public access blocked

## Step 1: Identify Resources

### Primary Resource

**S3 Bucket:**

- Type token: `aws:s3/bucket:Bucket`
- ID format: bucket name
- ID value: `nf-core-co2-reports`

### Related Resources

**Bucket Versioning:**

- Type token: `aws:s3/bucketVersioningV2:BucketVersioningV2`
- ID format: bucket name
- ID value: `nf-core-co2-reports`

**Encryption Configuration:**

- Type token: `aws:s3/bucketServerSideEncryptionConfigurationV2:BucketServerSideEncryptionConfigurationV2`
- ID format: bucket name
- ID value: `nf-core-co2-reports`

**Public Access Block:**

- Type token: `aws:s3/bucketPublicAccessBlock:BucketPublicAccessBlock`
- ID format: bucket name
- ID value: `nf-core-co2-reports`

## Step 2: Create Import JSON

Create `s3-import.json`:

```json
{
  "resources": [
    {
      "type": "aws:s3/bucket:Bucket",
      "name": "co2_reports_bucket",
      "id": "nf-core-co2-reports"
    },
    {
      "type": "aws:s3/bucketVersioningV2:BucketVersioningV2",
      "name": "co2_reports_versioning",
      "id": "nf-core-co2-reports"
    },
    {
      "type": "aws:s3/bucketServerSideEncryptionConfigurationV2:BucketServerSideEncryptionConfigurationV2",
      "name": "co2_reports_encryption",
      "id": "nf-core-co2-reports"
    },
    {
      "type": "aws:s3/bucketPublicAccessBlock:BucketPublicAccessBlock",
      "name": "co2_reports_public_block",
      "id": "nf-core-co2-reports"
    }
  ]
}
```

## Step 3: Execute Import

```bash
# Navigate to project
cd ~/src/nf-core/ops/pulumi/co2_reports

# Ensure credentials loaded
echo $AWS_ACCESS_KEY_ID  # Should show value
echo $PULUMI_CONFIG_PASSPHRASE  # Should show value

# Execute import
uv run pulumi import -f s3-import.json -o imported-s3.py -y
```

**Expected output:**

```
Importing (AWSMegatests)

View Live: https://app.pulumi.com/...

     Type                                                   Name                      Status
 +   pulumi:pulumi:Stack                                    co2_reports-AWSMegatests  created
 =   ├─ aws:s3/bucket:Bucket                               co2_reports_bucket        imported
 =   ├─ aws:s3/bucketVersioningV2:BucketVersioningV2       co2_reports_versioning    imported
 =   ├─ aws:s3/bucketServerSideEncryptionConfigurationV2   co2_reports_encryption    imported
 =   └─ aws:s3/bucketPublicAccessBlock:BucketPublicAccessBlock  co2_reports_public_block  imported

Resources:
    + 1 created
    = 4 imported
    5 changes

Duration: 12s
```

## Step 4: Review Generated Code

Check `imported-s3.py`:

```python
import pulumi
import pulumi_aws as aws

# Main bucket
co2_reports_bucket = aws.s3.Bucket(
    "co2_reports_bucket",
    bucket="nf-core-co2-reports",
    acl="private",
    tags={
        "Environment": pulumi.get_stack(),
        "Project": "co2-reports",
    }
)

# Versioning configuration
co2_reports_versioning = aws.s3.BucketVersioningV2(
    "co2_reports_versioning",
    bucket=co2_reports_bucket.id,
    versioning_configuration=aws.s3.BucketVersioningV2VersioningConfigurationArgs(
        status="Enabled",
    ),
)

# Encryption configuration
co2_reports_encryption = aws.s3.BucketServerSideEncryptionConfigurationV2(
    "co2_reports_encryption",
    bucket=co2_reports_bucket.id,
    rules=[aws.s3.BucketServerSideEncryptionConfigurationV2RuleArgs(
        apply_server_side_encryption_by_default=aws.s3.BucketServerSideEncryptionConfigurationV2RuleApplyServerSideEncryptionByDefaultArgs(
            sse_algorithm="AES256",
        ),
    )],
)

# Public access block
co2_reports_public_block = aws.s3.BucketPublicAccessBlock(
    "co2_reports_public_block",
    bucket=co2_reports_bucket.id,
    block_public_acls=True,
    block_public_policy=True,
    ignore_public_acls=True,
    restrict_public_buckets=True,
)

# Export outputs
pulumi.export("bucket_name", co2_reports_bucket.id)
pulumi.export("bucket_arn", co2_reports_bucket.arn)
```

## Step 5: Add to Pulumi Program

### Option A: Replace Existing Code

If `__main__.py` already has the bucket creation code, replace it:

```python
# __main__.py

"""Pulumi program for co2_reports infrastructure.

Imported Resources:
- nf-core-co2-reports S3 bucket
  Imported: 2025-01-02
  Originally created: 2024-11-15 for CO2 footprint tracking
  Import command: uv run pulumi import -f s3-import.json -y
"""

import pulumi
import pulumi_aws as aws
import pulumi_github as github
import pulumi_onepassword as onepassword

# Configuration
config = pulumi.Config()
aws_config = pulumi.Config("aws")
region = aws_config.require("region")

# === IMPORTED RESOURCES ===

# Main S3 bucket (imported from existing infrastructure)
bucket = aws.s3.Bucket(
    "co2_reports_bucket",
    bucket="nf-core-co2-reports",
    acl="private",
    tags={
        "Environment": pulumi.get_stack(),
        "Project": "co2-reports",
        "ManagedBy": "Pulumi",
        "Imported": "2025-01-02",
    },
    opts=pulumi.ResourceOptions(protect=True)  # Protect from accidental deletion
)

# Versioning (imported)
bucket_versioning = aws.s3.BucketVersioningV2(
    "co2_reports_versioning",
    bucket=bucket.id,
    versioning_configuration=aws.s3.BucketVersioningV2VersioningConfigurationArgs(
        status="Enabled",
    ),
)

# Encryption (imported)
bucket_encryption = aws.s3.BucketServerSideEncryptionConfigurationV2(
    "co2_reports_encryption",
    bucket=bucket.id,
    rules=[aws.s3.BucketServerSideEncryptionConfigurationV2RuleArgs(
        apply_server_side_encryption_by_default=aws.s3.BucketServerSideEncryptionConfigurationV2RuleApplyServerSideEncryptionByDefaultArgs(
            sse_algorithm="AES256",
        ),
    )],
)

# Public access block (imported)
bucket_public_block = aws.s3.BucketPublicAccessBlock(
    "co2_reports_public_block",
    bucket=bucket.id,
    block_public_acls=True,
    block_public_policy=True,
    ignore_public_acls=True,
    restrict_public_buckets=True,
)

# === NEW RESOURCES (if any) ===

# IAM user for CI/CD access
ci_user = aws.iam.User(
    "ci_user",
    name="nf-core-co2-reports-ci",
    tags={
        "Purpose": "CI/CD access to CO2 reports bucket",
    },
)

# Access key for CI user
access_key = aws.iam.AccessKey(
    "ci_access_key",
    user=ci_user.name,
)

# IAM policy for bucket access
policy = aws.iam.Policy(
    "bucket_access_policy",
    policy=bucket.arn.apply(lambda arn: json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:ListBucket",
                    "s3:GetBucketLocation"
                ],
                "Resource": arn,
                "Condition": {
                    "StringLike": {
                        "s3:prefix": ["modules/*"]
                    }
                }
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:PutObject",
                    "s3:GetObject"
                ],
                "Resource": f"{arn}/modules/*"
            }
        ]
    })),
)

# Attach policy to user
policy_attachment = aws.iam.UserPolicyAttachment(
    "ci_policy_attachment",
    user=ci_user.name,
    policy_arn=policy.arn,
)

# GitHub secrets for CI/CD
github.ActionsSecret(
    "aws_key_id",
    repository="modules",
    secret_name="CO2_REPORTS_AWS_ACCESS_KEY_ID",
    plaintext_value=access_key.id,
)

github.ActionsSecret(
    "aws_secret_key",
    repository="modules",
    secret_name="CO2_REPORTS_AWS_SECRET_ACCESS_KEY",
    plaintext_value=pulumi.Output.secret(access_key.secret),
)

github.ActionsVariable(
    "aws_region",
    repository="modules",
    variable_name="CO2_REPORTS_AWS_REGION",
    value=region,
)

# Export outputs
pulumi.export("bucket_name", bucket.id)
pulumi.export("bucket_arn", bucket.arn)
pulumi.export("ci_user_name", ci_user.name)
pulumi.export("access_key_id", access_key.id)
```

## Step 6: Verify Import

```bash
# Run preview - should show NO changes to imported resources
uv run pulumi preview
```

**Expected output:**

```
Previewing update (AWSMegatests)

View Live: https://app.pulumi.com/...

     Type                     Name                      Plan
     pulumi:pulumi:Stack      co2_reports-AWSMegatests
 ~   ├─ aws:iam/user:User     ci_user                   update
 ~   └─ ...                   ...                       ...

Resources:
    ~ 2 to update
    4 unchanged

Duration: 3s
```

✅ **Success**: Imported resources show as "unchanged"

## Step 7: Test Deployment

```bash
# Deploy any new changes
uv run pulumi up --yes

# Verify bucket still works
aws s3 ls s3://nf-core-co2-reports/ --region eu-north-1
```

## Common Issues

### Issue: Preview Shows Changes to Bucket

**Problem:**

```
~ aws:s3/bucket:Bucket: (update)
    [urn=urn:pulumi:AWSMegatests::co2_reports::aws:s3/bucket:Bucket::co2_reports_bucket]
  ~ acl: "private" => "public-read"
```

**Solution:** Generated code doesn't match actual configuration. Update code:

```python
bucket = aws.s3.Bucket(
    "co2_reports_bucket",
    bucket="nf-core-co2-reports",
    acl="private",  # Match actual ACL
    # Add any other properties shown in diff
)
```

### Issue: Import Fails - Bucket Not Found

**Problem:**

```
error: resource 'nf-core-co2-reports' not found
```

**Solutions:**

1. Verify bucket exists: `aws s3 ls s3://nf-core-co2-reports/`
2. Check region is correct in provider configuration
3. Verify AWS credentials have permission to access bucket

### Issue: Related Resources Not Imported

**Problem:** Versioning/encryption not included in import

**Solution:** Import each configuration separately:

```bash
uv run pulumi import aws:s3/bucketVersioningV2:BucketVersioningV2 co2_reports_versioning nf-core-co2-reports
uv run pulumi import aws:s3/bucketServerSideEncryptionConfigurationV2:BucketServerSideEncryptionConfigurationV2 co2_reports_encryption nf-core-co2-reports
```

## Next Steps

1. **Import IAM resources** if any exist for the bucket
2. **Import bucket policies** if configured
3. **Import lifecycle rules** if configured
4. **Test CI/CD integration** with imported bucket
5. **Document in README** what was imported and when

## Related Examples

- [AWS IAM Role Import](aws-iam-role.md) - Import IAM resources
- [GitHub Repository Import](github-repository.md) - Import GitHub settings
