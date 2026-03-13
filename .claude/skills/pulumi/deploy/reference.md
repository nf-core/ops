# Pulumi Deployment Reference

Comprehensive guide to advanced Pulumi deployment patterns and techniques.

## Table of Contents

- [Targeted Deployments](#targeted-deployments)
- [Refresh Operations](#refresh-operations)
- [Import Existing Infrastructure](#import-existing-infrastructure)
- [State Management](#state-management)
- [Parallel Deployments](#parallel-deployments)
- [CI/CD Integration](#cicd-integration)
- [Rollback Strategies](#rollback-strategies)
- [Performance Optimization](#performance-optimization)

## Targeted Deployments

Deploy specific resources without affecting the entire stack:

### Deploy Specific Resources

```bash
# Target a single resource
uv run pulumi up --target urn:pulumi:stack::project::aws:s3/bucket:Bucket::my-bucket

# Target multiple resources
uv run pulumi up --target bucket1 --target bucket2

# Preview targeted deployment
uv run pulumi preview --target resource-name
```

### Replace Specific Resources

Force recreation of a resource:

```bash
# Replace a specific resource
uv run pulumi up --replace urn:pulumi:stack::project::aws:ec2/instance:Instance::my-instance

# Preview replacement
uv run pulumi preview --replace resource-name
```

**Use cases:**

- Fix a misconfigured resource without full redeployment
- Test changes to specific components
- Minimize blast radius of changes

## Refresh Operations

Synchronize Pulumi state with actual infrastructure:

### Basic Refresh

```bash
# Detect and sync drift
uv run pulumi refresh

# Preview what refresh would do
uv run pulumi preview --refresh
```

### Refresh Without Update

```bash
# Only refresh state, don't apply changes
uv run pulumi refresh --yes

# Refresh and show differences
uv run pulumi refresh --diff
```

**When to refresh:**

- After manual infrastructure changes
- Before major deployments
- When state seems out of sync
- After infrastructure imports

## Import Existing Infrastructure

Bring existing resources under Pulumi management:

### Import Single Resource

```bash
# Import an existing S3 bucket
uv run pulumi import aws:s3/bucket:Bucket my-bucket existing-bucket-name

# Import with specific stack
uv run pulumi import --stack production aws:ec2/instance:Instance my-instance i-0123456789abcdef0
```

### Bulk Import

For multiple resources, create an import file:

```json
{
  "resources": [
    {
      "type": "aws:s3/bucket:Bucket",
      "name": "bucket1",
      "id": "my-bucket-1"
    },
    {
      "type": "aws:s3/bucket:Bucket",
      "name": "bucket2",
      "id": "my-bucket-2"
    }
  ]
}
```

```bash
# Import from file
uv run pulumi import --file imports.json
```

### Import Workflow

1. **Identify existing resources** to import
2. **Create Pulumi code** matching the existing resources
3. **Run import** command
4. **Verify state** with `pulumi stack --show-urns`
5. **Run preview** to ensure no changes
6. **Adjust code** if preview shows unexpected changes

## State Management

### Export State

```bash
# Export current stack state
uv run pulumi stack export > state-backup.json

# Export with secrets decrypted
uv run pulumi stack export --show-secrets > state-with-secrets.json
```

### Import State

```bash
# Restore from backup
uv run pulumi stack import --file state-backup.json
```

### Cancel Current Update

If deployment is stuck:

```bash
# Cancel in-progress update
uv run pulumi cancel
```

**⚠️ Warning**: Only use when absolutely necessary. Can leave stack in inconsistent state.

## Parallel Deployments

Optimize deployment speed:

### Configure Parallelism

```bash
# Increase parallel resource operations (default: 10)
uv run pulumi up --parallel 20

# Disable parallelism (sequential deployment)
uv run pulumi up --parallel 1
```

### Trade-offs

**Higher parallelism:**

- ✓ Faster deployments
- ✗ Higher API rate limits risk
- ✗ Harder to debug failures

**Lower parallelism:**

- ✓ More predictable
- ✓ Easier to debug
- ✗ Slower deployments

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy Infrastructure
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install uv
        run: pip install uv

      - name: Deploy with Pulumi
        run: uv run pulumi up --yes --stack production
        env:
          PULUMI_CONFIG_PASSPHRASE: ${{ secrets.PULUMI_CONFIG_PASSPHRASE }}
```

### Preview on Pull Request

```yaml
name: Preview Infrastructure Changes
on: pull_request

jobs:
  preview:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Preview with Pulumi
        run: |
          uv run pulumi preview --stack development > preview.txt
          cat preview.txt
        env:
          PULUMI_CONFIG_PASSPHRASE: ${{ secrets.PULUMI_CONFIG_PASSPHRASE }}

      - name: Comment Preview on PR
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const preview = fs.readFileSync('preview.txt', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## Pulumi Preview\n\`\`\`\n${preview}\n\`\`\``
            });
```

## Rollback Strategies

### Using Stack History

```bash
# List deployment history
uv run pulumi stack history

# Export previous state
uv run pulumi stack export --version <version-number> > previous-state.json

# Restore previous state
uv run pulumi stack import --file previous-state.json
```

### Git-Based Rollback

```bash
# Revert to previous commit
git revert HEAD
git push

# Deploy previous version
uv run pulumi up --yes
```

### Emergency Rollback

For critical issues:

1. **Export current state** for investigation
2. **Revert code** to last known good version
3. **Deploy immediately**: `uv run pulumi up --yes`
4. **Verify services** are restored
5. **Investigate** what went wrong

## Performance Optimization

### Reduce State File Size

```bash
# Remove deleted resources from state
uv run pulumi state delete urn:pulumi:stack::project::Type::name --yes
```

### Optimize Dependencies

Explicit dependencies improve parallelism:

```python
# Bad: Implicit dependencies
bucket = s3.Bucket("bucket")
object = s3.BucketObject("object", bucket=bucket.id)

# Good: Explicit dependencies enable better parallelism
bucket = s3.Bucket("bucket")
object = s3.BucketObject("object",
    bucket=bucket.id,
    opts=ResourceOptions(depends_on=[bucket])
)
```

### Stack Splitting

For large infrastructures, split into multiple stacks:

```
infrastructure/
├── networking/     # VPC, subnets, etc.
├── security/       # IAM, security groups
├── compute/        # EC2, ECS, Lambda
└── data/          # RDS, S3, DynamoDB
```

Benefits:

- Faster deployments (smaller state)
- Better separation of concerns
- Reduced blast radius
- Easier to manage permissions

### Use Stack References

Share outputs between stacks:

```python
# In networking stack
pulumi.export("vpc_id", vpc.id)

# In compute stack
networking = pulumi.StackReference("organization/networking/production")
vpc_id = networking.get_output("vpc_id")
```

## Best Practices Summary

1. **Always preview** before deploying
2. **Confirm with user** for production deployments
3. **Export state** before major changes
4. **Use targeted updates** when possible
5. **Refresh regularly** to detect drift
6. **Monitor deployments** in CI/CD
7. **Split large stacks** for performance
8. **Document changes** in git commits
9. **Test in development** first
10. **Have rollback plan** ready
