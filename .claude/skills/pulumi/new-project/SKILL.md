---
name: Creating New Pulumi Projects
description: Initialize new Pulumi projects with proper structure, dependencies, and 1Password credential management. Use when starting a new infrastructure project, scaffolding Pulumi setup, or creating infrastructure-as-code projects.
---

# Creating New Pulumi Projects

Scaffold new Pulumi projects with proper structure and configuration following nf-core/ops patterns.

## When to Use

Use this skill when:

- Starting a new infrastructure project
- Creating infrastructure-as-code for a service
- Scaffolding Pulumi project structure
- Setting up new environment (AWS, GitHub, etc.)
- Need template for Pulumi project setup

## Interactive Project Setup

### 1. Gather Requirements

Ask the user:

- **Project name**: What should the project be called? (e.g., `co2_reports`, `megatests_infra`)
- **Cloud provider**: Which provider? (AWS, Azure, GCP, GitHub, etc.)
- **Stack name**: Initial stack name? (e.g., `development`, `AWSMegatests`)
- **AWS region** (if applicable): Which region? (e.g., `us-east-1`, `eu-north-1`)
- **Description**: Brief description of infrastructure purpose
- **Additional providers**: Need GitHub, 1Password, or other providers?

### 2. Create Project Directory

```bash
# Navigate to pulumi projects directory
cd ~/src/nf-core/ops/pulumi

# Create project directory
mkdir {project_name}
cd {project_name}
```

### 3. Initialize Pulumi Project

```bash
# Initialize with Python
pulumi new python --yes --name {project_name} --description "{description}"

# Or manually create Pulumi.yaml (use template)
```

Use template from [templates/Pulumi.yaml](templates/Pulumi.yaml).

### 4. Set Up Project Files

Create the following files using templates:

#### pyproject.toml

Use [templates/pyproject.toml](templates/pyproject.toml) and customize:

- Project name
- Description
- Required providers
- Python version

#### .envrc

Use [templates/envrc.template](templates/envrc.template) and customize:

- AWS region (if applicable)
- 1Password vault references
- Additional environment variables

#### **main**.py

Use [templates/main_py.template](templates/main_py.template) as starting point:

- Import required providers
- Add infrastructure resources
- Export useful outputs

### 5. Install Dependencies

```bash
# Install with uv
uv sync

# Or with pip
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 6. Configure Credentials

```bash
# Allow direnv to load .envrc
direnv allow

# Verify credentials loaded
echo $AWS_ACCESS_KEY_ID
echo $PULUMI_CONFIG_PASSPHRASE
```

### 7. Initialize Stack

```bash
# Select or create stack
uv run pulumi stack init {stack_name}

# Set required configuration
uv run pulumi config set aws:region {region}

# Set additional config as needed
uv run pulumi config set {key} {value}
```

### 8. Initial Deployment

```bash
# Preview what will be created
uv run pulumi preview

# Deploy (after user confirms)
uv run pulumi up
```

## Project Structure

Standard structure for new projects:

```
project_name/
├── .envrc                  # Environment variables (1Password integration)
├── .python-version         # Python version (optional)
├── Pulumi.yaml             # Project configuration
├── Pulumi.{stack}.yaml     # Stack-specific configuration
├── __main__.py             # Infrastructure definition
├── pyproject.toml          # Python dependencies
├── uv.lock                 # Locked dependencies
├── README.md               # Project documentation
└── .venv/                  # Virtual environment (gitignored)
```

## Template Files

### Minimal pyproject.toml

```toml
[project]
name = "{project_name}"
version = "0.1.0"
description = "{description}"
readme = "README.md"
requires-python = ">=3.11"

dependencies = [
    "pulumi>=3.0.0,<4.0.0",
    "pulumi-aws>=6.0.0,<7.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Minimal .envrc

```bash
# Environment configuration for {project_name}
export OP_ACCOUNT=nf-core

# Load 1Password integration
source_url "https://github.com/tmatilai/direnv-1password/raw/v1.0.1/1password.sh" \
    "sha256-4dmKkmlPBNXimznxeehplDfiV+CvJiIzg7H1Pik4oqY="

# AWS credentials from 1Password
from_op AWS_ACCESS_KEY_ID="op://Dev/Pulumi-AWS-key/access key id"
from_op AWS_SECRET_ACCESS_KEY="op://Dev/Pulumi-AWS-key/secret access key"

# AWS Configuration
export AWS_REGION="{region}"
export AWS_DEFAULT_REGION="{region}"

# Pulumi passphrase
from_op PULUMI_CONFIG_PASSPHRASE="op://Employee/Pulumi Passphrase/password"
```

### Minimal **main**.py

```python
"""Pulumi program for {project_name}."""

import pulumi
import pulumi_aws as aws

# Get configuration
config = pulumi.Config()
aws_config = pulumi.Config("aws")
region = aws_config.require("region")

# Example: Create an S3 bucket
bucket = aws.s3.Bucket(
    "my-bucket",
    bucket=f"{pulumi.get_project()}-{pulumi.get_stack()}",
    acl="private",
    tags={
        "Environment": pulumi.get_stack(),
        "Project": pulumi.get_project(),
    },
)

# Export outputs
pulumi.export("bucket_name", bucket.id)
pulumi.export("bucket_arn", bucket.arn)
```

## Common Providers

### AWS

```bash
# Install provider
uv add pulumi-aws

# Configure
uv run pulumi config set aws:region us-east-1
```

### GitHub

```bash
# Install provider
uv add pulumi-github

# Configure
uv run pulumi config set github:owner nf-core
uv run pulumi config set github:token --secret
```

### 1Password

```bash
# Install provider
uv add pulumi-onepassword

# Configure service account token
uv run pulumi config set pulumi-onepassword:service_account_token --secret

# Or use .envrc:
export OP_SERVICE_ACCOUNT_TOKEN="your-token"
```

## Best Practices

### 1. Use Consistent Naming

Follow nf-core/ops conventions:

- Project names: `{service}_{purpose}` (e.g., `co2_reports`, `megatests_infra`)
- Stack names: environment or purpose (e.g., `development`, `AWSMegatests`)
- Resource names: descriptive and prefixed with project/stack

### 2. Document Everything

Create comprehensive README.md:

- What infrastructure is created
- How to deploy
- Required credentials
- Configuration options
- Troubleshooting tips

### 3. Use .envrc for Credentials

Always use 1Password + direnv pattern:

- Never commit credentials
- Consistent credential loading
- Easy to update credentials

### 4. Tag Resources

Add tags to all resources:

```python
tags={
    "Project": pulumi.get_project(),
    "Environment": pulumi.get_stack(),
    "ManagedBy": "Pulumi",
}
```

### 5. Export Useful Outputs

Export values other stacks or users might need:

```python
pulumi.export("vpc_id", vpc.id)
pulumi.export("subnet_ids", subnet_ids)
pulumi.export("endpoint_url", endpoint.url)
```

## Quick Start Checklist

When creating a new project:

- [ ] Create project directory
- [ ] Initialize Pulumi project (`pulumi new python`)
- [ ] Create pyproject.toml with dependencies
- [ ] Create .envrc with 1Password integration
- [ ] Write infrastructure code in **main**.py
- [ ] Install dependencies (`uv sync`)
- [ ] Allow direnv (`direnv allow`)
- [ ] Initialize stack (`pulumi stack init`)
- [ ] Set configuration (`pulumi config set`)
- [ ] Test preview (`pulumi preview`)
- [ ] Deploy (`pulumi up`)
- [ ] Create README.md documentation
- [ ] Commit to git

## Advanced Patterns

For more complex setups, see [reference.md](reference.md):

- Multi-stack projects
- Component resources
- Stack references
- Custom providers
- Testing strategies
- CI/CD integration

## Related Skills

- **Deploy**: Preview and deploy infrastructure changes
- **Stack Management**: Manage stacks and configuration
- **Documentation**: Access provider-specific documentation
