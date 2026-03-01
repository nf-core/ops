# Pulumi 1Password Provider Guide

Quick reference for accessing secrets from 1Password in Pulumi programs.

## Table of Contents

- [Authentication](#authentication)
- [Reading Secrets](#reading-secrets)
- [Common Patterns](#common-patterns)
- [Best Practices](#best-practices)

## Authentication

### Service Account Token

```bash
# Set via environment variable
export OP_SERVICE_ACCOUNT_TOKEN="ops_xxxxxxxxxxxxx"

# Or via Pulumi config
uv run pulumi config set pulumi-onepassword:service_account_token --secret
```

### Using direnv (Recommended)

```bash
# In .envrc
from_op OP_SERVICE_ACCOUNT_TOKEN="op://Employee/Service-Account/credential"
```

## Reading Secrets

### Basic Secret Access

```python
import pulumi_onepassword as onepassword

# Read a secret from 1Password
secret = onepassword.get_item_secret_output(
    vault="Dev",
    item="AWS-Key",
    field="password",
)

# Use in Pulumi resources
resource = SomeResource(
    "resource",
    secret_value=secret,
)
```

### Reading Specific Fields

```python
import pulumi_onepassword as onepassword

# Read access key ID
access_key_id = onepassword.get_item_secret_output(
    vault="Dev",
    item="AWS-Key",
    field="access key id",
)

# Read secret access key
secret_access_key = onepassword.get_item_secret_output(
    vault="Dev",
    item="AWS-Key",
    field="secret access key",
)

# Use in AWS provider
import pulumi_aws as aws

provider = aws.Provider(
    "aws-from-1password",
    access_key=access_key_id,
    secret_key=secret_access_key,
    region="us-east-1",
)
```

### Reading Multiple Secrets

```python
import pulumi_onepassword as onepassword

secrets = {
    "github_token": onepassword.get_item_secret_output(
        vault="Dev",
        item="GitHub-Token",
        field="credential",
    ),
    "database_password": onepassword.get_item_secret_output(
        vault="Dev",
        item="Database-Password",
        field="password",
    ),
    "api_key": onepassword.get_item_secret_output(
        vault="Dev",
        item="API-Key",
        field="credential",
    ),
}
```

## Common Patterns

### AWS Credentials from 1Password

```python
import pulumi_onepassword as onepassword
import pulumi_aws as aws

# Read AWS credentials
aws_access_key = onepassword.get_item_secret_output(
    vault="Dev",
    item="Pulumi-AWS-key",
    field="access key id",
)

aws_secret_key = onepassword.get_item_secret_output(
    vault="Dev",
    item="Pulumi-AWS-key",
    field="secret access key",
)

# Configure AWS provider
provider = aws.Provider(
    "aws",
    access_key=aws_access_key,
    secret_key=aws_secret_key,
    region="us-east-1",
)

# Create resource with provider
bucket = aws.s3.Bucket(
    "bucket",
    opts=pulumi.ResourceOptions(provider=provider),
)
```

### GitHub Token from 1Password

```python
import pulumi_onepassword as onepassword
import pulumi_github as github

# Read GitHub token
github_token = onepassword.get_item_secret_output(
    vault="Dev",
    item="GitHub-Token",
    field="credential",
)

# Configure GitHub provider
provider = github.Provider(
    "github",
    token=github_token,
    owner="nf-core",
)

# Create repository
repo = github.Repository(
    "repo",
    name="my-repo",
    opts=pulumi.ResourceOptions(provider=provider),
)
```

### Database Passwords

```python
import pulumi_onepassword as onepassword
import pulumi_aws as aws

# Read database password
db_password = onepassword.get_item_secret_output(
    vault="Dev",
    item="RDS-Master-Password",
    field="password",
)

# Create RDS instance
db = aws.rds.Instance(
    "postgres",
    engine="postgres",
    instance_class="db.t3.micro",
    allocated_storage=20,
    username="admin",
    password=db_password,
)
```

## Best Practices

### Vault Organization

Organize secrets by environment:

```
Vaults:
├── Dev             # Development secrets
├── Staging         # Staging environment secrets
├── Production      # Production secrets
└── Employee        # Personal/shared secrets
```

### Secret Naming

Use descriptive names:

```python
# Good
onepassword.get_item_secret_output(
    vault="Dev",
    item="Pulumi-AWS-Key",
    field="access key id",
)

# Bad
onepassword.get_item_secret_output(
    vault="Dev",
    item="key1",
    field="value",
)
```

### Environment-Specific Secrets

```python
import pulumi
import pulumi_onepassword as onepassword

stack = pulumi.get_stack()

# Map stack to vault
vault_map = {
    "development": "Dev",
    "staging": "Staging",
    "production": "Production",
}

vault = vault_map.get(stack, "Dev")

# Read from appropriate vault
secret = onepassword.get_item_secret_output(
    vault=vault,
    item="API-Key",
    field="credential",
)
```

### Caching Secrets

For frequently accessed secrets:

```python
import pulumi_onepassword as onepassword

# Read once
class Secrets:
    aws_access_key = onepassword.get_item_secret_output(
        vault="Dev",
        item="Pulumi-AWS-key",
        field="access key id",
    )
    aws_secret_key = onepassword.get_item_secret_output(
        vault="Dev",
        item="Pulumi-AWS-key",
        field="secret access key",
    )

# Reuse
provider1 = aws.Provider("provider1",
    access_key=Secrets.aws_access_key,
    secret_key=Secrets.aws_secret_key,
)

provider2 = aws.Provider("provider2",
    access_key=Secrets.aws_access_key,
    secret_key=Secrets.aws_secret_key,
)
```

## Alternative: Using direnv

For local development, prefer direnv over 1Password provider:

### .envrc Pattern

```bash
# .envrc
export OP_ACCOUNT=nf-core

source_url "https://github.com/tmatilai/direnv-1password/raw/v1.0.1/1password.sh" \
    "sha256-4dmKkmlPBNXimznxeehplDfiV+CvJiIzg7H1Pik4oqY="

# Load secrets from 1Password
from_op AWS_ACCESS_KEY_ID="op://Dev/Pulumi-AWS-key/access key id"
from_op AWS_SECRET_ACCESS_KEY="op://Dev/Pulumi-AWS-key/secret access key"
from_op PULUMI_CONFIG_PASSPHRASE="op://Employee/Pulumi Passphrase/password"
```

Then in Python code:

```python
import os

# Credentials available from environment
# (no 1Password provider needed)
aws_key = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")
```

### When to Use Each Approach

**Use 1Password Provider when:**

- Running in CI/CD without direnv
- Need to access secrets programmatically
- Sharing infrastructure code that needs secrets

**Use direnv + 1Password when:**

- Local development
- Interactive workflows
- Want credentials in environment for all tools

## Troubleshooting

### Service Account Not Found

**Error:**

```
error: [ERROR] 2025/01/02 service account not found
```

**Solution:**
Verify OP_SERVICE_ACCOUNT_TOKEN is set:

```bash
echo $OP_SERVICE_ACCOUNT_TOKEN
```

### Item Not Found

**Error:**

```
error: item "AWS-Key" not found in vault "Dev"
```

**Solutions:**

1. Check item name spelling
2. Verify vault name
3. Ensure service account has access to vault

### Field Not Found

**Error:**

```
error: field "password" not found in item
```

**Solution:**
Check field name in 1Password (exact match required):

```python
# Common field names:
- "password"
- "credential"
- "access key id"
- "secret access key"
- "username"
```

### Permission Denied

**Error:**

```
error: service account does not have permission to access item
```

**Solution:**
Grant service account access to vault in 1Password admin console.

## Example: Complete Infrastructure Setup

```python
"""Infrastructure using 1Password for all secrets."""
import pulumi
import pulumi_onepassword as onepassword
import pulumi_aws as aws
import pulumi_github as github

# Read AWS credentials
aws_key = onepassword.get_item_secret_output(
    vault="Dev",
    item="Pulumi-AWS-key",
    field="access key id",
)

aws_secret = onepassword.get_item_secret_output(
    vault="Dev",
    item="Pulumi-AWS-key",
    field="secret access key",
)

# Read GitHub token
github_token = onepassword.get_item_secret_output(
    vault="Dev",
    item="GitHub-Token",
    field="credential",
)

# Configure providers
aws_provider = aws.Provider(
    "aws",
    access_key=aws_key,
    secret_key=aws_secret,
    region="us-east-1",
)

github_provider = github.Provider(
    "github",
    token=github_token,
    owner="nf-core",
)

# Create resources
bucket = aws.s3.Bucket(
    "bucket",
    opts=pulumi.ResourceOptions(provider=aws_provider),
)

repo = github.Repository(
    "repo",
    name="my-repo",
    opts=pulumi.ResourceOptions(provider=github_provider),
)

# Store bucket info as GitHub secret
github.ActionsSecret(
    "bucket-name",
    repository=repo.name,
    secret_name="S3_BUCKET",
    plaintext_value=bucket.id,
    opts=pulumi.ResourceOptions(provider=github_provider),
)
```

## Documentation Links

- **1Password Provider**: https://www.pulumi.com/registry/packages/onepassword/
- **API Reference**: https://www.pulumi.com/registry/packages/onepassword/api-docs/
- **direnv-1password**: https://github.com/tmatilai/direnv-1password
