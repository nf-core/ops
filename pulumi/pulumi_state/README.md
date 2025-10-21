# Pulumi State Storage Bootstrap

Bootstrap project to create and manage the S3 bucket used for Pulumi state storage across all nf-core infrastructure projects.

## Purpose

This project creates an S3 bucket (`nf-core-pulumi-state`) that serves as the backend for all other Pulumi projects. It uses a **local backend** to avoid circular dependency issues.

## S3 Bucket Configuration

- **Bucket Name**: `nf-core-pulumi-state`
- **Region**: `eu-north-1` (Stockholm)
- **Versioning**: Enabled (keeps history of state changes)
- **Encryption**: AES-256 (SSE-S3)
- **Lifecycle**: Expires old versions after 90 days
- **Public Access**: Blocked
- **Purpose**: Pulumi state storage for all nf-core ops projects

## Initial Setup

```bash
# 1. Install dependencies
uv sync

# 2. Login to local backend (this project only)
pulumi login --local

# 3. Create production stack
pulumi stack init prod

# 4. Preview changes
uv run pulumi preview

# 5. Deploy the bucket
uv run pulumi up

# 6. View outputs
uv run pulumi stack output
```

## Manual S3 Bucket Setup (Alternative)

If you need to create the S3 bucket manually before using Pulumi (e.g., bootstrapping from scratch), use these AWS CLI commands:

### 1. Set Up AWS Credentials

Use 1Password to retrieve AWS credentials for the nf-core account:

```bash
# Set 1Password account context
export OP_ACCOUNT=nf-core

# Retrieve and export AWS credentials
export AWS_ACCESS_KEY_ID="$(op read 'op://Employee/Edmund Megatests AWS Creds/access key id')"
export AWS_SECRET_ACCESS_KEY="$(op read 'op://Employee/Edmund Megatests AWS Creds/secret access key')"
export AWS_DEFAULT_REGION="eu-north-1"
```

### 2. Create S3 Bucket

```bash
aws s3 mb s3://nf-core-pulumi-state --region eu-north-1
```

### 3. Configure Bucket Settings

**Enable Versioning:**
```bash
aws s3api put-bucket-versioning \
  --bucket nf-core-pulumi-state \
  --versioning-configuration Status=Enabled
```

**Enable Encryption:**
```bash
aws s3api put-bucket-encryption \
  --bucket nf-core-pulumi-state \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      },
      "BucketKeyEnabled": true
    }]
  }'
```

**Block Public Access:**
```bash
aws s3api put-public-access-block \
  --bucket nf-core-pulumi-state \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

**Configure Lifecycle Policy:**
```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket nf-core-pulumi-state \
  --lifecycle-configuration '{
    "Rules": [
      {
        "ID": "expire-old-versions",
        "Status": "Enabled",
        "Filter": {},
        "NoncurrentVersionExpiration": {
          "NoncurrentDays": 90
        }
      },
      {
        "ID": "abort-incomplete-multipart-uploads",
        "Status": "Enabled",
        "Filter": {},
        "AbortIncompleteMultipartUpload": {
          "DaysAfterInitiation": 7
        }
      }
    ]
  }'
```

**Add Tags:**
```bash
aws s3api put-bucket-tagging \
  --bucket nf-core-pulumi-state \
  --tagging 'TagSet=[
    {Key=Name,Value=nf-core-pulumi-state},
    {Key=project,Value=pulumi-state},
    {Key=managed-by,Value=pulumi},
    {Key=environment,Value=shared},
    {Key=purpose,Value=pulumi-state-storage}
  ]'
```

## Environment Variables

### Required for Manual Setup

When setting up the S3 bucket manually via AWS CLI:

```bash
# 1Password account (for credential retrieval)
export OP_ACCOUNT=nf-core

# AWS credentials (retrieved from 1Password)
export AWS_ACCESS_KEY_ID="$(op read 'op://Employee/Edmund Megatests AWS Creds/access key id')"
export AWS_SECRET_ACCESS_KEY="$(op read 'op://Employee/Edmund Megatests AWS Creds/secret access key')"

# AWS region for bucket
export AWS_DEFAULT_REGION="eu-north-1"
```

### Required for Other Pulumi Projects

Once the bucket is created, other Pulumi projects need:

```bash
# Option 1: Set backend URL as environment variable
export PULUMI_BACKEND_URL='s3://nf-core-pulumi-state?region=eu-north-1&awssdk=v2'

# Option 2: Use pulumi login command (recommended)
pulumi login 's3://nf-core-pulumi-state?region=eu-north-1&awssdk=v2'
```

**Note:** AWS credentials are still required to access the S3 bucket. Use the same 1Password credentials or configure via ESC/OIDC.

## Importing Existing Bucket into Pulumi

If you created the bucket manually and need to import it into Pulumi state:

```bash
# 1. Ensure you're logged into local backend
pulumi login --local

# 2. Select the prod stack
pulumi stack select prod

# 3. Import all bucket resources
pulumi import aws:s3/bucket:Bucket pulumi-state-bucket nf-core-pulumi-state
pulumi import aws:s3/bucketVersioningV2:BucketVersioningV2 state-bucket-versioning nf-core-pulumi-state
pulumi import aws:s3/bucketServerSideEncryptionConfigurationV2:BucketServerSideEncryptionConfigurationV2 state-bucket-encryption nf-core-pulumi-state
pulumi import aws:s3/bucketPublicAccessBlock:BucketPublicAccessBlock state-bucket-public-access-block nf-core-pulumi-state
pulumi import aws:s3/bucketLifecycleConfigurationV2:BucketLifecycleConfigurationV2 state-bucket-lifecycle nf-core-pulumi-state
```

**Resources Imported:**
- Main S3 bucket
- Bucket versioning configuration
- Server-side encryption configuration
- Public access block settings
- Lifecycle configuration

After importing, run `pulumi preview` to verify that no changes are detected.

## Usage in Other Projects

Once the bucket is created, other Pulumi projects can use it as their backend:

```bash
# Login to S3 backend
pulumi login s3://nf-core-pulumi-state

# Or with explicit region
pulumi login 's3://nf-core-pulumi-state?region=eu-north-1&awssdk=v2'
```

## State Location

This bootstrap project stores its state locally at:
```
~/.pulumi/stacks/pulumi-state/
```

All other projects store their state in:
```
s3://nf-core-pulumi-state/.pulumi/stacks/<project-name>/<stack-name>.json
```

## Architecture Decision

**Why local backend for this project?**

To avoid circular dependency:
- We need an S3 bucket to store Pulumi state
- We need Pulumi to create the S3 bucket
- Solution: Use local backend for this bootstrap project

**Is this a problem?**

No, because:
- This project is simple and rarely changes
- Local state is backed up in git (stack configs)
- Only bucket metadata is in state (bucket already exists after first deploy)

## Bucket Features

### Versioning
Keeps history of all state file versions. Useful for:
- Recovery from accidental corruption
- Auditing changes
- Rolling back if needed

### Encryption
All state files are encrypted at rest with AES-256.

### Lifecycle Policy
- Old versions expire after 90 days
- Incomplete multipart uploads cleaned up after 7 days

### Public Access
All public access is blocked to protect state files.

## Operations

### View Stack Outputs
```bash
uv run pulumi stack output
```

### Update Bucket Configuration
```bash
# Edit __main__.py
uv run pulumi preview
uv run pulumi up
```

### Destroy (⚠️ Use with caution)
```bash
# This will delete the bucket and all state files!
uv run pulumi destroy
```

## Migration from Pulumi Cloud

If migrating existing projects from Pulumi Cloud to S3:

```bash
# 1. Export state from Pulumi Cloud
pulumi stack export --file state.json

# 2. Login to S3 backend
pulumi login s3://nf-core-pulumi-state

# 3. Select or create stack
pulumi stack select <stack-name>

# 4. Import state
pulumi stack import --file state.json
```

## Team Access

Team members need:
- AWS credentials with S3 access
- Permissions to read/write to `nf-core-pulumi-state` bucket

IAM policy for team members:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketLocation",
        "s3:GetBucketVersioning"
      ],
      "Resource": "arn:aws:s3:::nf-core-pulumi-state"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::nf-core-pulumi-state/*"
    }
  ]
}
```

## Security Notes

- State files may contain sensitive information (resource IDs, configurations)
- Use Pulumi ESC or external secrets managers for sensitive values
- Never commit state files to git
- Ensure AWS credentials are properly secured

## Troubleshooting

### Bucket already exists
If the bucket exists but isn't in Pulumi state:
```bash
pulumi import aws:s3/bucket:Bucket pulumi-state-bucket nf-core-pulumi-state
```

### State file conflicts
S3 doesn't have built-in locking. For concurrent access:
- Use DynamoDB for state locking (requires additional setup)
- Coordinate deployments manually
- Consider using Pulumi Cloud for teams

## Related Projects

- `pulumi/seqera_platform/awsmegatests/` - Uses this S3 backend
- `pulumi/seqera_platform/resource_optimization/` - Uses this S3 backend
- `pulumi/AWSMegatests/` - Legacy project (migrating to S3 backend)
