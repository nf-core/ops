---
name: Accessing Pulumi Documentation
description: Access Pulumi documentation, provider guides, and troubleshooting resources. Use when looking up Pulumi syntax, provider-specific documentation, API references, or best practices for AWS, GitHub, 1Password, or other providers.
---

# Accessing Pulumi Documentation

Quick access to Pulumi documentation and provider-specific guides.

## When to Use

Use this skill when:

- Looking up Pulumi syntax or API
- Finding provider-specific documentation
- Checking resource properties
- Learning best practices
- Troubleshooting provider issues
- Finding code examples

## Quick Documentation Access

### Official Pulumi Docs

For latest documentation, use WebSearch:

```
Search: "Pulumi {topic} documentation 2025"
```

Examples:

- "Pulumi AWS S3 bucket documentation 2025"
- "Pulumi stack references documentation 2025"
- "Pulumi component resources guide 2025"

### Provider-Specific Guides

This skill includes cached guides for common providers:

- **AWS**: [providers/aws.md](providers/aws.md)
- **GitHub**: [providers/github.md](providers/github.md)
- **1Password**: [providers/onepassword.md](providers/onepassword.md)

Load the appropriate guide based on the user's question.

## Common Documentation Patterns

### Finding Resource Documentation

**AWS Resources:**

```
Search: "Pulumi AWS {resource} documentation"
# Examples:
- "Pulumi AWS EC2 Instance documentation"
- "Pulumi AWS RDS database documentation"
- "Pulumi AWS IAM policy documentation"
```

**GitHub Resources:**

```
Search: "Pulumi GitHub {resource} documentation"
# Examples:
- "Pulumi GitHub repository documentation"
- "Pulumi GitHub Actions secret documentation"
```

### Finding Examples

```
Search: "Pulumi {use case} example"
# Examples:
- "Pulumi Lambda function with API Gateway example"
- "Pulumi VPC with public and private subnets example"
- "Pulumi cross-stack reference example"
```

### Finding Best Practices

```
Search: "Pulumi {topic} best practices"
# Examples:
- "Pulumi project structure best practices"
- "Pulumi secret management best practices"
- "Pulumi testing best practices"
```

## Workflow for Documentation Questions

1. **Identify the topic**: What is the user asking about?
2. **Check if provider-specific**: Is it AWS, GitHub, 1Password specific?
3. **Load relevant guide**: If available in providers/ directory
4. **Search if needed**: Use WebSearch for latest docs
5. **Provide clear answer**: With code examples when relevant

## Common Questions

### How do I...?

**Create a resource:**

- Check providers/{provider}.md for examples
- Search: "Pulumi {provider} {resource} example"

**Configure authentication:**

- See [providers/aws.md](providers/aws.md) for AWS
- See [providers/github.md](providers/github.md) for GitHub

**Export outputs:**

```python
pulumi.export("output_name", resource.property)
```

**Reference another stack:**

```python
other_stack = pulumi.StackReference("org/project/stack")
value = other_stack.get_output("output_name")
```

**Use secrets:**

```python
config = pulumi.Config()
secret_value = config.require_secret("secret_key")
```

### What properties are available?

**Check documentation:**

```
Search: "Pulumi {provider} {resource} properties"
```

**Common pattern:**
Most resources have:

- `id`: Resource identifier
- `arn`: AWS Resource Name (AWS resources)
- `name`: Resource name
- `tags`: Resource tags

### How do I troubleshoot...?

See:

- [../stack-management/troubleshooting.md](../stack-management/troubleshooting.md) for common issues
- Provider-specific guides for provider issues

## Provider Registry

Access provider registries:

- **AWS**: https://www.pulumi.com/registry/packages/aws/
- **GitHub**: https://www.pulumi.com/registry/packages/github/
- **1Password**: https://www.pulumi.com/registry/packages/onepassword/
- **All providers**: https://www.pulumi.com/registry/

## Code Examples

### Basic Resource Creation

```python
import pulumi
import pulumi_aws as aws

# Create resource with explicit properties
bucket = aws.s3.Bucket(
    "my-bucket",
    bucket="my-unique-bucket-name",
    acl="private",
    tags={
        "Environment": pulumi.get_stack(),
    },
)

# Export output
pulumi.export("bucket_name", bucket.id)
```

### Using Configuration

```python
import pulumi

config = pulumi.Config()

# Get required value
region = config.require("region")

# Get optional value with default
instance_type = config.get("instance_type") or "t3.micro"

# Get boolean
enable_monitoring = config.get_bool("enable_monitoring") or False

# Get secret
database_password = config.require_secret("database_password")
```

### Resource Options

```python
from pulumi import ResourceOptions

# Explicit dependency
resource_b = aws.Resource("b",
    opts=ResourceOptions(depends_on=[resource_a])
)

# Use different provider
resource_eu = aws.Resource("eu",
    opts=ResourceOptions(provider=provider_eu)
)

# Protect from deletion
critical_resource = aws.Resource("critical",
    opts=ResourceOptions(protect=True)
)

# Custom timeout
long_running = aws.Resource("long",
    opts=ResourceOptions(
        custom_timeouts=CustomTimeouts(
            create="30m",
            update="20m",
            delete="10m",
        )
    )
)
```

## Quick Reference

| Task           | Resource                                             |
| -------------- | ---------------------------------------------------- |
| AWS docs       | [providers/aws.md](providers/aws.md)                 |
| GitHub docs    | [providers/github.md](providers/github.md)           |
| 1Password docs | [providers/onepassword.md](providers/onepassword.md) |
| Latest docs    | WebSearch: "Pulumi {topic} 2025"                     |
| Examples       | WebSearch: "Pulumi {use case} example"               |
| API reference  | https://www.pulumi.com/docs/reference/               |
| Registry       | https://www.pulumi.com/registry/                     |

## Advanced Topics

For complex scenarios, see [reference.md](reference.md):

- Dynamic providers
- Automation API
- Policy as code
- Testing frameworks
- Provider customization

## Related Skills

- **Deploy**: Preview and deploy infrastructure changes
- **Stack Management**: Manage stacks and configuration
- **New Project**: Initialize new Pulumi projects
