# Pulumi Import Reference

Advanced patterns and techniques for importing existing infrastructure into Pulumi.

## Table of Contents

- [Import Methods](#import-methods)
- [Automated Discovery](#automated-discovery)
- [Handling Dependencies](#handling-dependencies)
- [Large-Scale Import Strategies](#large-scale-import-strategies)
- [Provider-Specific Patterns](#provider-specific-patterns)
- [State Management](#state-management)
- [Troubleshooting](#troubleshooting)

## Import Methods

### CLI-Based Import (Recommended)

**Single resource:**

```bash
uv run pulumi import <type> <name> <id>
```

**Advantages:**

- Automatic code generation
- Immediate feedback
- Simple workflow
- Protection enabled by default

**Use when:**

- Importing few resources
- Learning import workflow
- Quick one-off imports

### Bulk Import

**Multiple resources from JSON:**

```bash
uv run pulumi import -f resources.json -o generated.py -y
```

**Advantages:**

- Efficient for many resources
- Declarative approach
- Can be scripted
- Generates organized code

**Use when:**

- Importing many resources
- Systematic migration
- Automated workflows

### Code-Based Import

**Using ResourceOptions:**

```python
bucket = aws.s3.Bucket(
    "existing-bucket",
    bucket="my-existing-bucket",
    opts=pulumi.ResourceOptions(import_="my-existing-bucket")
)
```

Then run `pulumi up` to import.

**Advantages:**

- Code-first approach
- Good for multi-stack scenarios
- Integrates with existing code

**Use when:**

- Managing multiple stacks
- Conditional imports
- Programmatic control needed

## Automated Discovery

### AWS Resource Discovery

Automate finding resources to import:

```python
#!/usr/bin/env python3
"""Discover AWS resources for Pulumi import."""

import boto3
import json
from typing import List, Dict

def discover_s3_buckets(region: str, prefix: str = "nf-core-") -> List[Dict]:
    """Discover S3 buckets matching prefix."""
    s3 = boto3.client('s3', region_name=region)
    buckets = s3.list_buckets()['Buckets']

    resources = []
    for bucket in buckets:
        if bucket['Name'].startswith(prefix):
            resources.append({
                "type": "aws:s3/bucket:Bucket",
                "name": bucket['Name'].replace(prefix, '').replace('-', '_'),
                "id": bucket['Name']
            })

            # Discover bucket configurations
            try:
                # Versioning
                versioning = s3.get_bucket_versioning(Bucket=bucket['Name'])
                if versioning.get('Status') == 'Enabled':
                    resources.append({
                        "type": "aws:s3/bucketVersioning:BucketVersioning",
                        "name": f"{bucket['Name'].replace(prefix, '').replace('-', '_')}_versioning",
                        "id": bucket['Name']
                    })
            except Exception as e:
                print(f"Warning: Could not check versioning for {bucket['Name']}: {e}")

    return resources

def discover_iam_roles(region: str, prefix: str = "nf-core-") -> List[Dict]:
    """Discover IAM roles matching prefix."""
    iam = boto3.client('iam', region_name=region)
    roles = iam.list_roles()['Roles']

    resources = []
    for role in roles:
        if role['RoleName'].startswith(prefix):
            resources.append({
                "type": "aws:iam/role:Role",
                "name": role['RoleName'].replace(prefix, '').replace('-', '_'),
                "id": role['RoleName']
            })

            # Discover attached policies
            try:
                policies = iam.list_attached_role_policies(RoleName=role['RoleName'])
                for policy in policies['AttachedPolicies']:
                    # Only import custom policies (not AWS managed)
                    if not policy['PolicyArn'].startswith('arn:aws:iam::aws:'):
                        resources.append({
                            "type": "aws:iam/policy:Policy",
                            "name": policy['PolicyName'].replace('-', '_'),
                            "id": policy['PolicyArn']
                        })
            except Exception as e:
                print(f"Warning: Could not check policies for {role['RoleName']}: {e}")

    return resources

def generate_import_json(resources: List[Dict], output_file: str):
    """Generate import JSON file."""
    import_data = {"resources": resources}

    with open(output_file, 'w') as f:
        json.dump(import_data, f, indent=2)

    print(f"Generated import file: {output_file}")
    print(f"Found {len(resources)} resources to import")

# Usage
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Discover AWS resources for Pulumi import')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--prefix', default='nf-core-', help='Resource name prefix')
    parser.add_argument('--resource-type', choices=['s3', 'iam', 'all'], default='all')
    parser.add_argument('--output', default='discovered-resources.json', help='Output JSON file')

    args = parser.parse_args()

    resources = []

    if args.resource_type in ['s3', 'all']:
        print(f"Discovering S3 buckets in {args.region}...")
        resources.extend(discover_s3_buckets(args.region, args.prefix))

    if args.resource_type in ['iam', 'all']:
        print(f"Discovering IAM roles...")
        resources.extend(discover_iam_roles(args.region, args.prefix))

    generate_import_json(resources, args.output)

    print(f"\nNext steps:")
    print(f"1. Review {args.output}")
    print(f"2. Run: uv run pulumi import -f {args.output} -o imported.py -y")
    print(f"3. Add generated code to your Pulumi program")
    print(f"4. Verify: uv run pulumi preview")
```

**Usage:**

```bash
# Discover all nf-core resources
python scripts/discover-aws-resources.py --region eu-west-1 --prefix nf-core-

# Import discovered resources
uv run pulumi import -f discovered-resources.json -o imported.py -y
```

### GitHub Resource Discovery

```python
#!/usr/bin/env python3
"""Discover GitHub resources for Pulumi import."""

import requests
import json
from typing import List, Dict

def discover_github_repos(org: str, token: str) -> List[Dict]:
    """Discover GitHub repositories in organization."""
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    url = f'https://api.github.com/orgs/{org}/repos'
    response = requests.get(url, headers=headers)
    repos = response.json()

    resources = []
    for repo in repos:
        resources.append({
            "type": "github:index/repository:Repository",
            "name": repo['name'].replace('-', '_'),
            "id": repo['full_name']
        })

    return resources

# Usage
if __name__ == "__main__":
    import os

    org = "nf-core"
    token = os.getenv("GITHUB_TOKEN")

    if not token:
        print("Error: GITHUB_TOKEN environment variable not set")
        exit(1)

    print(f"Discovering repositories in {org}...")
    resources = discover_github_repos(org, token)

    with open('github-repos.json', 'w') as f:
        json.dump({"resources": resources}, f, indent=2)

    print(f"Found {len(resources)} repositories")
    print("Run: uv run pulumi import -f github-repos.json -o imported-github.py -y")
```

## Handling Dependencies

### Parent-Child Relationships

When resources have parent-child relationships, specify parents in import JSON:

```json
{
  "resources": [
    {
      "type": "aws:s3/bucket:Bucket",
      "name": "my_bucket",
      "id": "my-bucket-name"
    },
    {
      "type": "aws:s3/bucketVersioning:BucketVersioning",
      "name": "my_bucket_versioning",
      "id": "my-bucket-name",
      "parent": "urn:pulumi:stack::project::aws:s3/bucket:Bucket::my_bucket"
    },
    {
      "type": "aws:s3/bucketPublicAccessBlock:BucketPublicAccessBlock",
      "name": "my_bucket_public_block",
      "id": "my-bucket-name",
      "parent": "urn:pulumi:stack::project::aws:s3/bucket:Bucket::my_bucket"
    }
  ]
}
```

**Finding parent URN:**

```bash
# Import parent first
uv run pulumi import aws:s3/bucket:Bucket my_bucket my-bucket-name

# Get parent URN
uv run pulumi stack --show-urns | grep my_bucket
```

### Import Order

Import resources in dependency order:

**Phase 1: Foundational Resources**

- VPCs
- S3 buckets
- IAM roles (without policies)

**Phase 2: Network Resources**

- Subnets
- Route tables
- Security groups

**Phase 3: Application Resources**

- EC2 instances
- ECS services
- Lambda functions

**Phase 4: Data Resources**

- RDS databases
- DynamoDB tables
- ElastiCache clusters

### Cross-Resource Dependencies

Use explicit dependencies in generated code:

```python
# Import bucket
bucket = aws.s3.Bucket("bucket", bucket="my-bucket")

# Import policy that depends on bucket
policy = aws.iam.Policy(
    "bucket_policy",
    policy=bucket.arn.apply(lambda arn: json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": "s3:GetObject",
            "Resource": f"{arn}/*"
        }]
    })),
    opts=pulumi.ResourceOptions(depends_on=[bucket])
)
```

## Large-Scale Import Strategies

### Phased Approach

**Phase 1: Discovery (Week 1)**

- Audit existing infrastructure
- Document resources by project/application
- Identify dependencies
- Generate import JSON files

**Phase 2: Foundational Import (Week 2)**

- Import VPCs, S3 buckets, base IAM roles
- Verify imports
- Set up protection
- Document in code

**Phase 3: Application Import (Week 3-4)**

- Import compute resources
- Import application-specific resources
- Verify all integrations
- Test deployments

**Phase 4: Cleanup (Week 5)**

- Remove unused resources
- Consolidate duplicate resources
- Optimize resource organization
- Update documentation

### Organization Patterns

**Option A: Separate Import Project**

```
pulumi/
├── existing-infrastructure/     # Imported resources
│   ├── __main__.py
│   └── Pulumi.yaml
└── new-infrastructure/          # New resources
    ├── __main__.py
    └── Pulumi.yaml
```

**Option B: Mixed in Existing Project**

```python
# __main__.py

# === Imported Resources ===
imported_bucket = aws.s3.Bucket(
    "imported_megatests",
    bucket="nf-core-awsmegatests",
    # ... imported properties ...
)

# === New Resources ===
new_bucket = aws.s3.Bucket(
    "new_co2_reports",
    bucket=f"nf-core-co2-reports-{pulumi.get_stack()}",
    # ... new configuration ...
)
```

**Option C: By Domain**

```
pulumi/
├── networking/         # VPCs, subnets (imported + new)
├── storage/           # S3, EFS (imported + new)
├── compute/           # EC2, ECS (imported + new)
└── data/             # RDS, DynamoDB (imported + new)
```

### Batch Processing

For very large imports:

```bash
# Split into batches of 50 resources
split -l 50 all-resources.json batch-

# Import each batch
for batch in batch-*; do
    echo "Importing $batch..."
    uv run pulumi import -f "$batch" -y
    sleep 5  # Rate limiting
done
```

## Provider-Specific Patterns

### AWS S3 Complete Infrastructure

Import bucket with all configurations:

```json
{
  "resources": [
    {
      "type": "aws:s3/bucket:Bucket",
      "name": "my_bucket",
      "id": "my-bucket-name"
    },
    {
      "type": "aws:s3/bucketVersioningV2:BucketVersioningV2",
      "name": "my_bucket_versioning",
      "id": "my-bucket-name"
    },
    {
      "type": "aws:s3/bucketServerSideEncryptionConfigurationV2:BucketServerSideEncryptionConfigurationV2",
      "name": "my_bucket_encryption",
      "id": "my-bucket-name"
    },
    {
      "type": "aws:s3/bucketPublicAccessBlock:BucketPublicAccessBlock",
      "name": "my_bucket_public_block",
      "id": "my-bucket-name"
    },
    {
      "type": "aws:s3/bucketLifecycleConfigurationV2:BucketLifecycleConfigurationV2",
      "name": "my_bucket_lifecycle",
      "id": "my-bucket-name"
    }
  ]
}
```

### AWS IAM Role with Policies

```json
{
  "resources": [
    {
      "type": "aws:iam/role:Role",
      "name": "lambda_role",
      "id": "my-lambda-execution-role"
    },
    {
      "type": "aws:iam/policy:Policy",
      "name": "lambda_policy",
      "id": "arn:aws:iam::123456789:policy/my-lambda-policy"
    },
    {
      "type": "aws:iam/rolePolicyAttachment:RolePolicyAttachment",
      "name": "lambda_attach",
      "id": "my-lambda-execution-role/arn:aws:iam::123456789:policy/my-lambda-policy"
    }
  ]
}
```

### GitHub Repository with Settings

```bash
# Import repository
uv run pulumi import github:index/repository:Repository ops_repo nf-core/ops

# Import branch protection
uv run pulumi import github:index/branchProtection:BranchProtection ops_main_protection "nf-core/ops:main"

# Import team access
uv run pulumi import github:index/teamRepository:TeamRepository ops_team_access "12345:nf-core/ops"
```

## State Management

### Backup Before Import

Always backup state before large imports:

```bash
# Export current state
uv run pulumi stack export > pre-import-backup.json

# Perform import
uv run pulumi import -f resources.json -y

# If issues occur, restore
uv run pulumi stack import --file pre-import-backup.json
```

### State Verification

After import, verify state integrity:

```bash
# List all resources
uv run pulumi stack --show-urns

# Check for orphaned resources
uv run pulumi refresh

# Verify no pending changes
uv run pulumi preview
```

### Removing Imported Resources

If you need to remove imported resources from Pulumi management without deleting them:

```bash
# Remove from state but keep in cloud
uv run pulumi state delete <urn> --yes

# Example
uv run pulumi state delete urn:pulumi:production::project::aws:s3/bucket:Bucket::old_bucket --yes
```

## Troubleshooting

### Import Fails with "Resource Already Exists"

**Problem:** Resource already managed by another Pulumi stack or Terraform

**Solutions:**

1. Check if resource is in another stack
2. If migrating from Terraform, remove from Terraform state first
3. Verify not already imported

### Generated Code Doesn't Match

**Problem:** Preview shows changes after adding generated code

**Solutions:**

1. **Check for auto-naming**: Explicitly set resource names

```python
# Bad
bucket = aws.s3.Bucket("bucket")  # Pulumi adds random suffix

# Good
bucket = aws.s3.Bucket("bucket", bucket="actual-bucket-name")
```

2. **Add missing properties**: Include ALL properties from generated code

3. **Check provider configuration**: Ensure region/account match

### Dependency Import Errors

**Problem:** Cannot import child resource without parent

**Solutions:**

1. Import parent first
2. Use parent URN in import JSON
3. Import resources in correct order

### Protection Errors

**Problem:** Cannot delete/replace protected imported resource

**Solutions:**

1. **Disable protection temporarily:**

```python
opts=pulumi.ResourceOptions(protect=False)
```

2. **Or use state commands:**

```bash
uv run pulumi state unprotect <urn>
```

### Large Import Timeouts

**Problem:** Import times out for many resources

**Solutions:**

1. Break into smaller batches
2. Increase timeout: `--timeout 30m`
3. Import incrementally

## Best Practices Summary

1. **Audit first**: Know what you're importing before starting
2. **Start small**: Import incrementally, test as you go
3. **Backup state**: Always export state before large imports
4. **Verify always**: Run preview after every import
5. **Protect resources**: Enable protection on critical resources
6. **Document imports**: Record what, when, why in code comments
7. **Use discovery**: Automate finding resources with scripts
8. **Test thoroughly**: Verify integrations after import
9. **Clean up**: Remove unused resources after import
10. **Train team**: Ensure team understands import workflow
