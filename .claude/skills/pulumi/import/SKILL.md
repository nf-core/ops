---
name: Importing Existing Infrastructure
description: Import manually created "click-ops" resources into Pulumi management. Use when bringing existing AWS, GitHub, or other cloud resources under infrastructure-as-code control. Supports single resource and bulk import workflows with automatic code generation.
---

# Importing Existing Infrastructure

Bring manually created "click-ops" infrastructure under Pulumi management safely and systematically.

## When to Use

Use this skill when:

- Migrating manually created cloud resources to infrastructure-as-code
- Bringing "click-ops" resources under version control
- Consolidating infrastructure from console/CLI creation to Pulumi
- Adopting Pulumi for existing infrastructure
- Taking over infrastructure created by others

## Quick Single Resource Import

### Step 1: Identify Resource

Find the resource type token and ID:

1. **Go to Pulumi Registry**: https://www.pulumi.com/registry/
2. **Search for resource** (e.g., "AWS S3 Bucket")
3. **Find Import section** in documentation
4. **Copy type token** and **identify ID format**

**Example:**

- Resource: S3 bucket named `nf-core-co2-reports`
- Type token: `aws:s3/bucket:Bucket`
- ID (lookup property): `nf-core-co2-reports`

### Step 2: Import Resource

```bash
# Navigate to Pulumi project
cd ~/src/nf-core/ops/pulumi/co2_reports

# Import resource
uv run pulumi import <type> <name> <id>

# Example:
uv run pulumi import aws:s3/bucket:Bucket co2-reports-bucket nf-core-co2-reports
```

### Step 3: Add Generated Code

Pulumi automatically generates code for the resource:

```python
# Copy generated code snippet into __main__.py
bucket = aws.s3.Bucket("co2-reports-bucket",
    bucket="nf-core-co2-reports",
    # ... generated properties ...
)
```

### Step 4: Verify Import

```bash
# Run preview - should show NO changes
uv run pulumi preview

# If changes shown, adjust code to match actual configuration
```

## Bulk Import Workflow

For importing multiple resources efficiently:

### Step 1: Create Import JSON File

```json
{
  "resources": [
    {
      "type": "aws:s3/bucket:Bucket",
      "name": "co2-reports-bucket",
      "id": "nf-core-co2-reports"
    },
    {
      "type": "aws:s3/bucketVersioning:BucketVersioning",
      "name": "co2-reports-versioning",
      "id": "nf-core-co2-reports"
    },
    {
      "type": "aws:s3/bucketPublicAccessBlock:BucketPublicAccessBlock",
      "name": "co2-reports-public-block",
      "id": "nf-core-co2-reports"
    }
  ]
}
```

Save as `resources-to-import.json`.

### Step 2: Execute Bulk Import

```bash
# Import all resources and generate code
uv run pulumi import -f resources-to-import.json -o imported-resources.py -y
```

Options:

- `-f`: Input JSON file
- `-o`: Output file for generated code
- `-y`: Auto-approve without prompts

### Step 3: Integrate Generated Code

```bash
# Review generated code
cat imported-resources.py

# Copy relevant sections to your __main__.py
# Adapt as needed for your project structure
```

### Step 4: Verify All Imports

```bash
# Preview should show NO changes
uv run pulumi preview

# View imported resources in state
uv run pulumi stack --show-urns
```

## Import Verification Checklist

After importing, verify:

- [ ] All resources appear in `pulumi stack --show-urns`
- [ ] `pulumi preview` shows **no changes**
- [ ] Generated code added to `__main__.py`
- [ ] Resource names match actual cloud resource names
- [ ] Dependencies between resources are correct
- [ ] Critical resources are protected (`protect=True`)
- [ ] Documentation added (what was imported and why)

## Safety Guidelines

### Protection

Always protect critical imported resources:

```python
bucket = aws.s3.Bucket(
    "production-bucket",
    bucket="nf-core-production-data",
    opts=pulumi.ResourceOptions(protect=True)  # Prevent accidental deletion
)
```

### Verification

**Never skip verification:**

```bash
# ALWAYS run preview after import
uv run pulumi preview

# If changes shown, code doesn't match cloud reality
# Adjust code until preview shows no changes
```

### Documentation

Document imports in code:

```python
"""
Imported Resources:
- nf-core-co2-reports bucket: Imported 2025-01-02
  Originally created 2024-11-15 for CO2 footprint tracking
  Import command: uv run pulumi import aws:s3/bucket:Bucket co2-reports-bucket nf-core-co2-reports
"""
```

## Common Resource Imports

### AWS S3 Bucket

```bash
# Type token: aws:s3/bucket:Bucket
# ID format: bucket name
uv run pulumi import aws:s3/bucket:Bucket my-bucket existing-bucket-name
```

### AWS IAM Role

```bash
# Type token: aws:iam/role:Role
# ID format: role name
uv run pulumi import aws:iam/role:Role my-role existing-role-name
```

### AWS EC2 Instance

```bash
# Type token: aws:ec2/instance:Instance
# ID format: instance ID (i-xxxxxxxxxxxx)
uv run pulumi import aws:ec2/instance:Instance my-instance i-0123456789abcdef0
```

### GitHub Repository

```bash
# Type token: github:index/repository:Repository
# ID format: repository name (owner/repo)
uv run pulumi import github:index/repository:Repository my-repo nf-core/ops
```

## Troubleshooting

### Import Fails: Resource Not Found

**Problem:** `error: resource not found`

**Solutions:**

1. Verify resource exists in cloud
2. Check correct region/account (provider configuration)
3. Verify ID format is correct (check Pulumi Registry)

### Preview Shows Changes After Import

**Problem:** `pulumi preview` shows changes despite import

**Solutions:**

1. Generated code missing properties - add all properties from generated code
2. Property values don't match - adjust code to match actual values
3. Auto-naming mismatch - ensure explicit names specified

### Dependency Errors

**Problem:** `error: resource depends on another resource`

**Solutions:**

1. Import parent resources first
2. Specify parent in import JSON
3. Import resources in dependency order

See [../stack-management/troubleshooting.md](../stack-management/troubleshooting.md) for more issues.

## Advanced Patterns

For complex import scenarios, see [reference.md](reference.md):

- Automated resource discovery
- Large-scale bulk imports
- Handling complex dependencies
- Import with parent resources
- Cross-stack imports
- State management after import

## Examples

See detailed provider-specific examples:

- [AWS S3 Bucket Import](examples/aws-s3-bucket.md) - Complete S3 infrastructure
- [AWS IAM Role Import](examples/aws-iam-role.md) - Roles and policies
- [GitHub Repository Import](examples/github-repository.md) - Repository and settings

## Helper Scripts

Discover resources for import:

```bash
# AWS resource discovery
python scripts/discover-aws-resources.py --region eu-west-1 --resource-type s3

# Generates import JSON file automatically
```

See [scripts/discover-aws-resources.py](scripts/discover-aws-resources.py) for details.

## Related Skills

- **Deploy**: Deploy infrastructure after import
- **Stack Management**: Organize imported resources across stacks
- **Documentation**: Find type tokens and import IDs
- **New Project**: Create projects for imported infrastructure
