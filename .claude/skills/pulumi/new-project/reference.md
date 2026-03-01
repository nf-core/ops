# Pulumi New Project Reference

Advanced patterns for structuring and organizing Pulumi projects.

## Table of Contents

- [Project Organization](#project-organization)
- [Component Resources](#component-resources)
- [Multi-Stack Projects](#multi-stack-projects)
- [Testing Strategies](#testing-strategies)
- [CI/CD Integration](#cicd-integration)
- [Configuration Management](#configuration-management)
- [Provider Configuration](#provider-configuration)

## Project Organization

### Single-Stack Projects

Simple projects with one environment:

```
simple_project/
├── .envrc
├── Pulumi.yaml
├── Pulumi.development.yaml
├── __main__.py
└── pyproject.toml
```

### Multi-Stack Projects

Projects with multiple environments:

```
multi_env_project/
├── .envrc
├── Pulumi.yaml
├── Pulumi.development.yaml
├── Pulumi.staging.yaml
├── Pulumi.production.yaml
├── __main__.py
├── pyproject.toml
└── config/
    ├── development.py
    ├── staging.py
    └── production.py
```

### Component-Based Projects

Large projects with reusable components:

```
large_project/
├── .envrc
├── Pulumi.yaml
├── Pulumi.production.yaml
├── __main__.py
├── pyproject.toml
├── components/
│   ├── __init__.py
│   ├── networking.py
│   ├── compute.py
│   └── storage.py
└── utils/
    ├── __init__.py
    └── tags.py
```

## Component Resources

Create reusable infrastructure components:

### Basic Component

```python
import pulumi
import pulumi_aws as aws
from pulumi import ComponentResource, ResourceOptions


class WebServer(ComponentResource):
    def __init__(self, name: str, vpc_id: str, subnet_id: str, opts=None):
        super().__init__("custom:WebServer", name, {}, opts)

        # Security group
        self.security_group = aws.ec2.SecurityGroup(
            f"{name}-sg",
            vpc_id=vpc_id,
            ingress=[
                aws.ec2.SecurityGroupIngressArgs(
                    protocol="tcp",
                    from_port=80,
                    to_port=80,
                    cidr_blocks=["0.0.0.0/0"],
                ),
            ],
            opts=ResourceOptions(parent=self),
        )

        # EC2 instance
        self.instance = aws.ec2.Instance(
            f"{name}-instance",
            instance_type="t3.micro",
            subnet_id=subnet_id,
            vpc_security_group_ids=[self.security_group.id],
            opts=ResourceOptions(parent=self),
        )

        self.register_outputs({
            "instance_id": self.instance.id,
            "public_ip": self.instance.public_ip,
        })


# Usage
web_server = WebServer("app", vpc_id=vpc.id, subnet_id=subnet.id)
pulumi.export("web_server_ip", web_server.instance.public_ip)
```

### Component with Configuration

```python
from dataclasses import dataclass
from typing import Optional


@dataclass
class WebServerArgs:
    vpc_id: str
    subnet_id: str
    instance_type: str = "t3.micro"
    enable_monitoring: bool = False
    tags: Optional[dict] = None


class WebServer(ComponentResource):
    def __init__(self, name: str, args: WebServerArgs, opts=None):
        super().__init__("custom:WebServer", name, {}, opts)

        tags = args.tags or {}

        # Create resources with args
        self.instance = aws.ec2.Instance(
            f"{name}-instance",
            instance_type=args.instance_type,
            subnet_id=args.subnet_id,
            monitoring=args.enable_monitoring,
            tags=tags,
            opts=ResourceOptions(parent=self),
        )

        self.register_outputs({"instance_id": self.instance.id})
```

## Multi-Stack Projects

### Environment-Specific Configuration

Create config files for each environment:

```python
# config/base.py
BASE_CONFIG = {
    "instance_type": "t3.micro",
    "enable_monitoring": False,
}

# config/production.py
from .base import BASE_CONFIG

PRODUCTION_CONFIG = {
    **BASE_CONFIG,
    "instance_type": "m5.large",
    "enable_monitoring": True,
    "backup_retention_days": 30,
}

# config/development.py
from .base import BASE_CONFIG

DEVELOPMENT_CONFIG = {
    **BASE_CONFIG,
    "backup_retention_days": 7,
}
```

Use in **main**.py:

```python
import pulumi
from config.development import DEVELOPMENT_CONFIG
from config.production import PRODUCTION_CONFIG

stack = pulumi.get_stack()

# Load config based on stack
if stack == "production":
    env_config = PRODUCTION_CONFIG
elif stack == "staging":
    env_config = STAGING_CONFIG
else:
    env_config = DEVELOPMENT_CONFIG

# Use config
instance = aws.ec2.Instance(
    "app",
    instance_type=env_config["instance_type"],
    monitoring=env_config["enable_monitoring"],
)
```

### Stack-Specific Resources

```python
import pulumi

stack = pulumi.get_stack()

# Only create monitoring in production
if stack == "production":
    alarm = aws.cloudwatch.MetricAlarm(
        "high-cpu",
        comparison_operator="GreaterThanThreshold",
        evaluation_periods=2,
        metric_name="CPUUtilization",
        namespace="AWS/EC2",
        period=120,
        statistic="Average",
        threshold=80,
    )
```

## Testing Strategies

### Unit Tests

Test individual components:

```python
# tests/test_webserver.py
import unittest
from unittest.mock import Mock, patch
import pulumi


class WebServerTests(unittest.TestCase):
    @patch("pulumi.runtime.is_dry_run", return_value=True)
    def test_webserver_creation(self, mock_dry_run):
        # Test component creation
        pass
```

### Integration Tests

Test full deployments:

```bash
#!/bin/bash
# test_deployment.sh

set -e

# Create test stack
pulumi stack init test-${RANDOM}

# Deploy
pulumi up --yes

# Verify outputs
BUCKET_NAME=$(pulumi stack output bucket_name)
aws s3 ls s3://${BUCKET_NAME}

# Cleanup
pulumi destroy --yes
pulumi stack rm --yes
```

### Preview Tests

Test that preview succeeds:

```bash
# In CI/CD
uv run pulumi preview --expect-no-changes
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Deploy Infrastructure

on:
  push:
    branches: [main]
    paths:
      - "**.py"
      - "Pulumi*.yaml"
      - "pyproject.toml"

jobs:
  preview:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install uv
          uv sync

      - name: Preview changes
        run: uv run pulumi preview --stack development
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          PULUMI_CONFIG_PASSPHRASE: ${{ secrets.PULUMI_CONFIG_PASSPHRASE }}

  deploy:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install uv
          uv sync

      - name: Deploy to production
        run: uv run pulumi up --yes --stack production
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          PULUMI_CONFIG_PASSPHRASE: ${{ secrets.PULUMI_CONFIG_PASSPHRASE }}
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pulumi-preview
        name: Pulumi Preview
        entry: uv run pulumi preview
        language: system
        pass_filenames: false
        always_run: false
        files: \.(py|yaml)$
```

## Configuration Management

### Hierarchical Configuration

Load config from multiple sources:

```python
import os
import pulumi
from pathlib import Path

# 1. Default values
config = {
    "instance_type": "t3.micro",
    "region": "us-east-1",
}

# 2. Pulumi config (stack-specific)
pulumi_config = pulumi.Config()
config["instance_type"] = pulumi_config.get("instance_type") or config["instance_type"]

# 3. Environment variables
config["region"] = os.getenv("AWS_REGION", config["region"])

# 4. File-based config
config_file = Path("config.json")
if config_file.exists():
    import json
    file_config = json.loads(config_file.read_text())
    config.update(file_config)
```

### Secret Management

Best practices for secrets:

```python
import pulumi

config = pulumi.Config()

# Use Pulumi secrets
database_password = config.require_secret("database_password")

# Or load from 1Password via environment
import os
api_key = os.getenv("API_KEY")  # Loaded by direnv from 1Password

# Never hardcode secrets
# BAD: database_password = "hardcoded123"
```

## Provider Configuration

### Multiple Provider Instances

Use multiple AWS accounts or regions:

```python
import pulumi_aws as aws

# Default provider (us-east-1)
bucket_east = aws.s3.Bucket("bucket-east")

# Secondary provider (eu-west-1)
provider_eu = aws.Provider("eu-west-1",
    region="eu-west-1"
)

bucket_eu = aws.s3.Bucket("bucket-eu",
    opts=pulumi.ResourceOptions(provider=provider_eu)
)
```

### Assume Role

```python
import pulumi_aws as aws

# Provider with assumed role
provider_prod = aws.Provider("production",
    region="us-east-1",
    assume_role=aws.ProviderAssumeRoleArgs(
        role_arn="arn:aws:iam::123456789:role/PulumiDeploy",
        session_name="pulumi-deploy",
    ),
)

# Use provider
bucket = aws.s3.Bucket("prod-bucket",
    opts=pulumi.ResourceOptions(provider=provider_prod)
)
```

## Best Practices

1. **Component Resources**: Use for reusable infrastructure patterns
2. **Configuration Files**: Separate config from code
3. **Testing**: Test infrastructure code like application code
4. **CI/CD**: Automate deployments and previews
5. **Secrets**: Never commit secrets, use encryption or external stores
6. **Documentation**: Document components and configurations
7. **Tags**: Tag all resources consistently
8. **Outputs**: Export useful information for other stacks or users
9. **Dependencies**: Explicit dependencies improve reliability
10. **Monitoring**: Add observability from the start
