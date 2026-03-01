# Importing AWS IAM Roles and Policies

Import existing IAM roles, policies, and their attachments into Pulumi.

## Scenario: Import CI User and Policy

Import the `nf-core-co2-reports-ci` IAM user and its associated policy.

### Resources to Import

1. **IAM User**: `nf-core-co2-reports-ci`
2. **IAM Policy**: `nf-core-co2-reports-bucket-access`
3. **Policy Attachment**: User to Policy attachment

## Step 1: Discover Resources

### Find IAM User

```bash
# List users
aws iam list-users | jq '.Users[] | select(.UserName | contains("nf-core"))'

# Get user details
aws iam get-user --user-name nf-core-co2-reports-ci
```

### Find Attached Policies

```bash
# List attached policies
aws iam list-attached-user-policies --user-name nf-core-co2-reports-ci

# Get policy ARN and details
aws iam get-policy --policy-arn arn:aws:iam::728131696474:policy/nf-core-co2-reports-bucket-access
```

## Step 2: Create Import JSON

Create `iam-import.json`:

```json
{
  "resources": [
    {
      "type": "aws:iam/user:User",
      "name": "ci_user",
      "id": "nf-core-co2-reports-ci"
    },
    {
      "type": "aws:iam/policy:Policy",
      "name": "bucket_access_policy",
      "id": "arn:aws:iam::728131696474:policy/nf-core-co2-reports-bucket-access"
    },
    {
      "type": "aws:iam/userPolicyAttachment:UserPolicyAttachment",
      "name": "ci_policy_attachment",
      "id": "nf-core-co2-reports-ci/arn:aws:iam::728131696474:policy/nf-core-co2-reports-bucket-access"
    }
  ]
}
```

**Note:** UserPolicyAttachment ID format is `{user-name}/{policy-arn}`

## Step 3: Execute Import

```bash
cd ~/src/nf-core/ops/pulumi/co2_reports

# Import resources
uv run pulumi import -f iam-import.json -o imported-iam.py -y
```

## Step 4: Review Generated Code

Example generated code in `imported-iam.py`:

```python
import pulumi
import pulumi_aws as aws
import json

# IAM User
ci_user = aws.iam.User(
    "ci_user",
    name="nf-core-co2-reports-ci",
    tags={
        "Purpose": "CI/CD",
    },
)

# IAM Policy
bucket_access_policy = aws.iam.Policy(
    "bucket_access_policy",
    name="nf-core-co2-reports-bucket-access",
    description="Write access to modules/ prefix in nf-core-co2-reports S3 bucket for CI/CD",
    policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:ListBucket",
                    "s3:GetBucketLocation"
                ],
                "Resource": "arn:aws:s3:::nf-core-co2-reports",
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
                "Resource": "arn:aws:s3:::nf-core-co2-reports/modules/*"
            }
        ]
    }),
)

# Policy Attachment
ci_policy_attachment = aws.iam.UserPolicyAttachment(
    "ci_policy_attachment",
    user=ci_user.name,
    policy_arn=bucket_access_policy.arn,
)
```

## Step 5: Add to Program with Protection

Add to `__main__.py` with protection enabled:

```python
# === IMPORTED IAM RESOURCES ===

# CI User (imported - protect from deletion)
ci_user = aws.iam.User(
    "ci_user",
    name="nf-core-co2-reports-ci",
    tags={
        "Purpose": "CI/CD access to CO2 reports bucket",
        "Imported": "2025-01-02",
    },
    opts=pulumi.ResourceOptions(protect=True)  # Critical resource
)

# Bucket access policy (imported)
bucket_access_policy = aws.iam.Policy(
    "bucket_access_policy",
    name="nf-core-co2-reports-bucket-access",
    description="Write access to modules/ prefix in nf-core-co2-reports S3 bucket for CI/CD",
    policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:ListBucket",
                    "s3:GetBucketLocation"
                ],
                "Resource": "arn:aws:s3:::nf-core-co2-reports",
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
                "Resource": "arn:aws:s3:::nf-core-co2-reports/modules/*"
            }
        ]
    }),
    opts=pulumi.ResourceOptions(protect=True)
)

# Attach policy to user (imported)
ci_policy_attachment = aws.iam.UserPolicyAttachment(
    "ci_policy_attachment",
    user=ci_user.name,
    policy_arn=bucket_access_policy.arn,
)
```

## Step 6: Import Access Keys (Optional)

**⚠️ Warning:** Access keys cannot be imported because the secret key is not retrievable after creation.

**Options:**

1. **Leave existing keys** in place (don't manage with Pulumi)
2. **Create new keys** with Pulumi and rotate in GitHub secrets
3. **Delete old keys** after creating new ones

### Creating New Access Keys

```python
# Create new access key (Pulumi-managed)
access_key = aws.iam.AccessKey(
    "ci_access_key",
    user=ci_user.name,
)

# Update GitHub secrets with new keys
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

# Export for verification
pulumi.export("access_key_id", access_key.id)
```

## Step 7: Verify Import

```bash
# Preview - should show no changes to imported resources
uv run pulumi preview

# Check imported resources
uv run pulumi stack --show-urns | grep iam
```

## Advanced: Import IAM Role with Trust Policy

For IAM roles (like Lambda execution roles):

### Discover Role

```bash
# Get role details
aws iam get-role --role-name my-lambda-execution-role

# Get attached policies
aws iam list-attached-role-policies --role-name my-lambda-execution-role

# Get inline policies
aws iam list-role-policies --role-name my-lambda-execution-role
```

### Import JSON

```json
{
  "resources": [
    {
      "type": "aws:iam/role:Role",
      "name": "lambda_execution_role",
      "id": "my-lambda-execution-role"
    },
    {
      "type": "aws:iam/rolePolicyAttachment:RolePolicyAttachment",
      "name": "lambda_basic_execution",
      "id": "my-lambda-execution-role/arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
    }
  ]
}
```

### Generated Code

```python
# IAM Role
lambda_execution_role = aws.iam.Role(
    "lambda_execution_role",
    name="my-lambda-execution-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }]
    }),
)

# Attach AWS managed policy
lambda_basic_execution = aws.iam.RolePolicyAttachment(
    "lambda_basic_execution",
    role=lambda_execution_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
)
```

## Common Issues

### Issue: Policy ARN Not Found

**Problem:**

```
error: policy 'arn:aws:iam::123:policy/my-policy' not found
```

**Solution:** Verify policy exists and ARN is correct:

```bash
aws iam list-policies --scope Local | jq '.Policies[] | select(.PolicyName=="my-policy")'
```

### Issue: Attachment Import Fails

**Problem:**

```
error: attachment not found with id 'user/policy-arn'
```

**Solution:** Import user and policy first, then attachment:

```bash
# Import in order
uv run pulumi import aws:iam/user:User ci_user nf-core-co2-reports-ci
uv run pulumi import aws:iam/policy:Policy policy arn:aws:iam::123:policy/my-policy
uv run pulumi import aws:iam/userPolicyAttachment:UserPolicyAttachment attachment "nf-core-co2-reports-ci/arn:aws:iam::123:policy/my-policy"
```

### Issue: Policy Document Changes

**Problem:** Preview shows policy document changes

**Solution:** Format policy JSON consistently:

```python
# Use json.dumps for consistent formatting
policy=json.dumps({
    "Version": "2012-10-17",
    "Statement": [...]
}, indent=2, sort_keys=True)
```

## Best Practices

1. **Always protect IAM resources**: `protect=True`
2. **Document trust relationships**: Comment assume role policies
3. **Group related resources**: Import role with all its attachments
4. **Rotate access keys**: Create new keys with Pulumi, delete old ones
5. **Audit permissions**: Review imported policies for least privilege
6. **Test access**: Verify CI/CD still works after import

## Related Examples

- [AWS S3 Bucket Import](aws-s3-bucket.md) - Import S3 resources
- [GitHub Repository Import](github-repository.md) - Import GitHub settings
