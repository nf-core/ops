# Pulumi Stack Management Reference

Advanced stack management patterns and techniques.

## Table of Contents

- [Stack Organization](#stack-organization)
- [Cross-Stack References](#cross-stack-references)
- [Stack Tags](#stack-tags)
- [Stack Exports and Imports](#stack-exports-and-imports)
- [Stack Migrations](#stack-migrations)
- [Organization Management](#organization-management)
- [Configuration Strategies](#configuration-strategies)
- [Secret Management](#secret-management)

## Stack Organization

### Naming Conventions

**Environment-based:**

```
myproject-dev
myproject-staging
myproject-production
```

**Region-based:**

```
myproject-us-east-1
myproject-eu-west-1
myproject-ap-southeast-1
```

**Feature-based:**

```
myproject-networking
myproject-compute
myproject-data
```

**Combined:**

```
myproject-production-us-east-1
myproject-staging-eu-west-1
```

### Stack Hierarchy

For complex infrastructures:

```
organization/
├── shared/
│   ├── networking-production
│   ├── networking-staging
│   └── security
├── product-a/
│   ├── app-production
│   └── app-staging
└── product-b/
    ├── api-production
    └── api-staging
```

## Cross-Stack References

Share outputs between stacks:

### Export from Source Stack

```python
# In networking stack
import pulumi

vpc = aws.ec2.Vpc("vpc", cidr_block="10.0.0.0/16")

# Export for other stacks to use
pulumi.export("vpc_id", vpc.id)
pulumi.export("public_subnet_ids", [s.id for s in public_subnets])
pulumi.export("private_subnet_ids", [s.id for s in private_subnets])
```

### Import in Target Stack

```python
# In application stack
import pulumi

# Reference networking stack
networking_stack = pulumi.StackReference("organization/networking-stack/production")

# Get outputs
vpc_id = networking_stack.get_output("vpc_id")
public_subnet_ids = networking_stack.get_output("public_subnet_ids")

# Use in resources
instance = aws.ec2.Instance("app-server",
    instance_type="t3.medium",
    vpc_security_group_ids=[sg.id],
    subnet_id=public_subnet_ids[0]
)
```

### Stack Reference Format

```
<organization>/<project>/<stack>
```

Examples:

```python
pulumi.StackReference("acme-corp/networking/production")
pulumi.StackReference("my-org/databases/staging")
pulumi.StackReference("shared/security/global")
```

## Stack Tags

Organize and filter stacks with tags:

###Add Tags to Stack

```bash
# Tag stack with environment
uv run pulumi stack tag set environment production

# Tag with team ownership
uv run pulumi stack tag set team platform-team

# Tag with cost center
uv run pulumi stack tag set cost-center engineering
```

### View Stack Tags

```bash
# List all tags for current stack
uv run pulumi stack tag ls

# Get specific tag value
uv run pulumi stack tag get environment
```

### Remove Tags

```bash
# Remove a tag
uv run pulumi stack tag rm old-tag
```

### Using Tags

Tags help with:

- **Cost allocation**: Track spending by team or project
- **Automation**: Filter stacks in scripts
- **Organization**: Group related stacks
- **Compliance**: Track compliance requirements

## Stack Exports and Imports

### Export Stack State

```bash
# Export stack to JSON
uv run pulumi stack export > stack-backup.json

# Export with secrets decrypted
uv run pulumi stack export --show-secrets > stack-full-backup.json

# Export specific version
uv run pulumi stack export --version 42 > stack-v42.json
```

### Import Stack State

```bash
# Import stack state
uv run pulumi stack import --file stack-backup.json
```

### Use Cases

**Backup before major changes:**

```bash
uv run pulumi stack export > backup-$(date +%Y%m%d-%H%M%S).json
uv run pulumi up
```

**Migration between backends:**

```bash
# Export from old backend
uv run pulumi stack export > migration.json

# Switch backend
export PULUMI_BACKEND_URL="s3://new-backend"

# Import to new backend
uv run pulumi stack import --file migration.json
```

## Stack Migrations

### Rename Stack

```bash
# Export current state
uv run pulumi stack export > old-stack.json

# Create new stack
uv run pulumi stack init new-name

# Import state
uv run pulumi stack import --file old-stack.json

# Verify
uv run pulumi preview  # Should show no changes

# Remove old stack
uv run pulumi stack select old-name
uv run pulumi stack rm old-name --force
```

### Merge Stacks

Combine multiple stacks:

1. **Export both stacks**
2. **Manually merge JSON** (careful with dependencies)
3. **Import merged state**
4. **Run preview** to verify
5. **Remove old stacks**

**Note**: Complex operation - test thoroughly in development first!

### Split Stack

Separate monolithic stack:

1. **Create new stacks** for each component
2. **Move resources** to new code
3. **Use stack references** for dependencies
4. **Deploy new stacks**
5. **Remove resources** from old stack
6. **Destroy old stack**

## Organization Management

### Organization-Level Operations

```bash
# List all stacks in organization
pulumi stack ls --organization my-org

# Select stack with org prefix
uv run pulumi stack select my-org/project/stack
```

### Team Collaboration

**Access Control:**

- Use Pulumi Cloud for team access management
- Define roles: Admin, Editor, Viewer
- Audit access regularly

**CI/CD Integration:**

- Use service accounts for automation
- Rotate credentials regularly
- Limit permissions to minimum required

## Configuration Strategies

### Hierarchical Configuration

**Project-level config** (`Pulumi.yaml`):

```yaml
name: myproject
runtime: python
description: My infrastructure project
```

**Stack-level config** (`Pulumi.<stack>.yaml`):

```yaml
config:
  aws:region: us-east-1
  myproject:instance_type: t3.medium
  myproject:enable_monitoring: "true"
```

**Environment variables:**

```bash
export PULUMI_CONFIG_PASSPHRASE="secret"
export AWS_REGION="us-east-1"
```

### Configuration Patterns

**Shared defaults:**

```python
# config.py
import pulumi

config = pulumi.Config()

# Defaults
INSTANCE_TYPE = config.get("instance_type") or "t3.small"
REGION = config.require("aws:region")
MONITORING = config.get_bool("enable_monitoring") or False
```

**Environment-specific overrides:**

```python
import pulumi

stack = pulumi.get_stack()

if stack == "production":
    instance_type = "m5.large"
    enable_monitoring = True
elif stack == "staging":
    instance_type = "t3.medium"
    enable_monitoring = True
else:  # development
    instance_type = "t3.micro"
    enable_monitoring = False
```

## Secret Management

### Using Pulumi Secrets

```bash
# Set secret value
uv run pulumi config set database_password mypassword --secret

# Set secret from file
cat password.txt | uv run pulumi config set database_password --secret

# View secret (requires passphrase)
uv run pulumi config get database_password --show-secrets
```

### Using 1Password

Via .envrc and direnv:

```bash
# .envrc
from_op DATABASE_PASSWORD="op://Dev/Database/password"
from_op API_KEY="op://Dev/API-Keys/key"
```

Then in Pulumi code:

```python
import os
import pulumi

# Get from environment (loaded by direnv from 1Password)
database_password = os.getenv("DATABASE_PASSWORD")

# Or use Pulumi config
config = pulumi.Config()
api_key = config.get("api_key") or os.getenv("API_KEY")
```

### Secret Rotation

```bash
# Update secret
uv run pulumi config set database_password new-password --secret

# Deploy with new secret
uv run pulumi up
```

### Secrets in Stack Exports

```bash
# Export without secrets (encrypted)
uv run pulumi stack export > backup.json

# Export with decrypted secrets (keep secure!)
uv run pulumi stack export --show-secrets > backup-with-secrets.json
```

## Best Practices

1. **Use consistent naming**: Follow naming conventions across all stacks
2. **Tag everything**: Add tags for organization and cost tracking
3. **Document dependencies**: Use stack references for clear relationships
4. **Regular exports**: Backup stack state before major changes
5. **Limit stack scope**: Don't make stacks too large
6. **Separate environments**: Use different stacks for dev/staging/prod
7. **Automate**: Use CI/CD for stack management
8. **Monitor**: Track stack health and resource counts
9. **Clean up**: Remove unused stacks regularly
10. **Secure secrets**: Use encryption and access controls
