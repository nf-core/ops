# Pulumi Documentation Reference

Advanced topics and comprehensive documentation resources.

## Table of Contents

- [Core Concepts](#core-concepts)
- [Advanced Features](#advanced-features)
- [Testing and Quality](#testing-and-quality)
- [Performance](#performance)
- [Official Resources](#official-resources)

## Core Concepts

### Resource Model

Pulumi resources follow a declarative model:

1. **Inputs**: Configuration provided to resource
2. **Outputs**: Computed values from resource
3. **Dependencies**: Automatic or explicit resource relationships
4. **State**: Current infrastructure state tracked by Pulumi

### Output Values

Outputs are Promise-like values resolved during deployment:

```python
import pulumi

# Outputs are not immediately available
bucket = aws.s3.Bucket("bucket")

# Use apply() to work with output values
bucket_name = bucket.id.apply(lambda name: f"full-name-{name}")

# Or use in other resources directly
object = aws.s3.BucketObject("object",
    bucket=bucket.id,  # Pulumi handles dependency automatically
)
```

### Resource Options

Control resource behavior:

```python
from pulumi import ResourceOptions, CustomTimeouts

resource = Resource("name",
    opts=ResourceOptions(
        # Parent-child relationship
        parent=parent_resource,

        # Explicit dependencies
        depends_on=[other_resource],

        # Provider instance
        provider=custom_provider,

        # Protect from deletion
        protect=True,

        # Ignore changes to fields
        ignore_changes=["tags"],

        # Custom timeouts
        custom_timeouts=CustomTimeouts(
            create="30m",
            update="20m",
            delete="10m",
        ),

        # Replace on changes
        replace_on_changes=["*"],
    ),
)
```

## Advanced Features

### Dynamic Providers

Create custom resource providers:

```python
from pulumi.dynamic import Resource, ResourceProvider, CreateResult

class MyProvider(ResourceProvider):
    def create(self, inputs):
        # Custom create logic
        return CreateResult(id_="unique-id", outs=inputs)

    def update(self, id, old_inputs, new_inputs):
        # Custom update logic
        return UpdateResult(outs=new_inputs)

    def delete(self, id, props):
        # Custom delete logic
        pass

class MyResource(Resource):
    def __init__(self, name, props, opts=None):
        super().__init__(MyProvider(), name, props, opts)
```

### Automation API

Programmatically manage Pulumi operations:

```python
import pulumi.automation as auto

# Create or select stack
stack = auto.create_or_select_stack(
    stack_name="dev",
    project_name="my-project",
    program=lambda: None,  # Your Pulumi program
)

# Set configuration
stack.set_config("aws:region", auto.ConfigValue(value="us-east-1"))

# Run operations
up_result = stack.up()
print(f"Update summary: {up_result.summary}")

# Destroy
stack.destroy()
```

### Policy as Code

Enforce compliance with policies:

```python
# policy.py
from pulumi_policy import (
    EnforcementLevel,
    PolicyPack,
    ResourceValidationArgs,
    ResourceValidationPolicy,
)

def s3_bucket_encryption(args: ResourceValidationArgs, report_violation):
    if args.resource_type == "aws:s3/bucket:Bucket":
        encryption = args.props.get("serverSideEncryptionConfiguration")
        if not encryption:
            report_violation("S3 buckets must have encryption enabled")

PolicyPack(
    name="aws-compliance",
    enforcement_level=EnforcementLevel.MANDATORY,
    policies=[
        ResourceValidationPolicy(
            name="s3-bucket-encryption",
            description="Require S3 bucket encryption",
            validate=s3_bucket_encryption,
        ),
    ],
)
```

### Transformations

Modify resources automatically:

```python
import pulumi

def add_tags(args):
    if args.type_.startswith("aws:"):
        args.props["tags"] = args.props.get("tags", {})
        args.props["tags"]["ManagedBy"] = "Pulumi"
        args.props["tags"]["Stack"] = pulumi.get_stack()
    return pulumi.ResourceTransformationResult(
        props=args.props,
        opts=args.opts,
    )

# Apply transformation to all resources
pulumi.runtime.register_stack_transformation(add_tags)
```

## Testing and Quality

### Unit Testing

Test component resources:

```python
import unittest
from unittest.mock import patch, Mock
import pulumi


class TestInfrastructure(unittest.TestCase):
    @pulumi.runtime.test
    def test_bucket_creation(self):
        import __main__ as program

        # Mock resources
        def check_bucket(args):
            assert args.bucket.startswith("my-project-")
            assert args.acl == "private"

        pulumi.runtime.set_mocks(BucketMocks())

        # Import program triggers resource creation
        # Verify expectations in check_bucket
```

### Integration Testing

Test actual deployments:

```bash
#!/bin/bash
# integration_test.sh

# Create test stack
pulumi stack init test-$RANDOM

# Deploy
pulumi up --yes

# Run tests against deployed infrastructure
python tests/integration_tests.py

# Cleanup
pulumi destroy --yes
pulumi stack rm --yes
```

### Property Testing

Test resource properties:

```python
@pulumi.runtime.test
def test_all_buckets_private():
    import __main__ as program

    def check_bucket(args):
        if args.type_ == "aws:s3/bucket:Bucket":
            assert args.props["acl"] == "private", \
                f"Bucket {args.name} is not private"

    # Verify all buckets are private
```

## Performance

### Parallel Operations

```python
import pulumi

# Create multiple resources in parallel
buckets = []
for i in range(10):
    bucket = aws.s3.Bucket(f"bucket-{i}")
    buckets.append(bucket)

# Pulumi handles parallelization automatically
```

### Resource Providers

Use resource providers for large-scale operations:

```python
# Don't create providers repeatedly
# BAD:
for region in regions:
    provider = aws.Provider(region, region=region)
    bucket = aws.s3.Bucket("bucket", opts=ResourceOptions(provider=provider))

# GOOD: Reuse providers
providers = {region: aws.Provider(region, region=region) for region in regions}
for region in regions:
    bucket = aws.s3.Bucket(f"bucket-{region}",
        opts=ResourceOptions(provider=providers[region])
    )
```

### Reduce State Operations

```bash
# Skip refresh for faster previews
pulumi preview --skip-refresh

# Reduce parallelism if hitting rate limits
pulumi up --parallel 5
```

## Official Resources

### Documentation

- **Main Docs**: https://www.pulumi.com/docs/
- **Get Started**: https://www.pulumi.com/docs/get-started/
- **Concepts**: https://www.pulumi.com/docs/intro/concepts/
- **API Reference**: https://www.pulumi.com/docs/reference/

### Providers

- **Registry**: https://www.pulumi.com/registry/
- **AWS**: https://www.pulumi.com/registry/packages/aws/
- **GitHub**: https://www.pulumi.com/registry/packages/github/
- **1Password**: https://www.pulumi.com/registry/packages/onepassword/

### Examples

- **Examples Repo**: https://github.com/pulumi/examples
- **AWS Examples**: https://github.com/pulumi/examples/tree/master/aws-py-*
- **Tutorials**: https://www.pulumi.com/docs/tutorials/

### Community

- **Slack**: https://slack.pulumi.com
- **GitHub Discussions**: https://github.com/pulumi/pulumi/discussions
- **Stack Overflow**: https://stackoverflow.com/questions/tagged/pulumi

### Learning

- **Pulumi Learn**: https://www.pulumi.com/learn/
- **Blog**: https://www.pulumi.com/blog/
- **Videos**: https://www.pulumi.com/resources/

## Quick Tips

1. **Use WebSearch** for latest documentation
2. **Check provider docs** for resource properties
3. **Read examples** for common patterns
4. **Test in development** before production
5. **Use TypeScript/Python** for better IDE support
6. **Enable logging** for debugging (--logtostderr -v=9)
7. **Join Slack** for community help
8. **Read changelogs** for breaking changes
9. **Use stack references** for modular infrastructure
10. **Document your infrastructure** in code comments
