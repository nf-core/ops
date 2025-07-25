# AWS Megatests - Claude Code Context

This file provides Claude Code with context for the AWS Megatests Pulumi infrastructure project.

## Project Overview

This is a **Pulumi Infrastructure as Code (IaC) project** that manages AWS infrastructure for nf-core megatests. The project integrates multiple technologies:

- **Pulumi**: Python-based infrastructure as code
- **seqerakit**: CLI tool for Seqera Platform compute environment management
- **1Password**: Secret management via Pulumi provider
- **GitHub**: Automated secrets deployment for CI/CD workflows

## Architecture

### Core Components

1. **S3 Bucket Management**
   - Imports existing `nf-core-awsmegatests` bucket
   - Manages bucket configuration through Pulumi

2. **Seqera Compute Environments**
   - Three AWS Batch environments: CPU, ARM, GPU
   - Deployed via seqerakit integration with Pulumi commands
   - All environments have fusion snapshots enabled

3. **GitHub Secrets Automation**
   - Automatically pushes compute environment IDs to GitHub organization secrets
   - Manages Seqera Platform access tokens for CI/CD

4. **1Password Integration**
   - Secure credential management using Pulumi 1Password provider
   - Service account token for automated access

### File Structure

```
AWSMegatests/
├── __main__.py                 # Main Pulumi program
├── requirements.txt            # Python dependencies
├── Pulumi.yaml                # Pulumi project configuration
├── .envrc                     # Environment variables (1Password integration)
├── README.md                  # Project documentation
├── CLAUDE.md                  # This file - Claude context
└── seqerakit/                 # Seqerakit configurations
    ├── README.md              # Seqerakit-specific documentation
    ├── CLAUDE.md              # Seqerakit-specific Claude context
    ├── *.yml                  # Seqerakit YAML configurations
    └── *.json                 # Compute environment JSON specs
```

## Common Commands

### Prerequisites

```bash
# Install UV and dependencies
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync

# Install direnv for 1Password integration
brew install direnv
direnv allow

# Login to Pulumi
pulumi login
```

### Development Workflow

```bash
# Preview changes (must use direnv exec for AWS credentials)
direnv exec . uv run pulumi preview

# Deploy infrastructure
direnv exec . uv run pulumi up

# View outputs
direnv exec . uv run pulumi stack output

# Refresh state to match actual infrastructure
direnv exec . uv run pulumi refresh

# Import existing resources
direnv exec . uv run pulumi import <resource-type> <name> <id>
```

### State Management

```bash
# List stack resources
direnv exec . uv run pulumi stack --show-urns

# Unprotect resources
direnv exec . uv run pulumi state unprotect <urn>

# Remove resources from state (without deleting from cloud)
direnv exec . uv run pulumi state delete <urn>

# Protect critical resources
direnv exec . uv run pulumi state protect <urn>
```

## Key Technologies

### Pulumi Providers Used

1. **AWS Provider** (`pulumi-aws`)
   - Manages S3 bucket and related resources
   - Uses environment variables for authentication

2. **1Password Provider** (`pulumi-onepassword`)
   - Retrieves secrets from 1Password vaults
   - Uses service account token for authentication

3. **GitHub Provider** (`pulumi-github`)
   - Manages organization secrets
   - Requires GitHub token with appropriate permissions

4. **Command Provider** (`pulumi-command`)
   - Executes seqerakit CLI commands
   - Manages compute environment deployment lifecycle

### Environment Variables

The `.envrc` file manages both static configuration and 1Password secret references:

**Static Variables:**
```bash
export ORGANIZATION_NAME="nf-core"
export WORKSPACE_NAME="AWSmegatests"
export AWS_REGION="eu-west-1"
export AWS_WORK_DIR="s3://nf-core-awsmegatests"
export AWS_CREDENTIALS_NAME="tower-awstest"
export AWS_COMPUTE_ENV_ALLOWED_BUCKETS="s3://ngi-igenomes,s3://annotation-cache"
```

**1Password Secret References:**
```bash
from_op TOWER_ACCESS_TOKEN="op://Dev/zwsrkl26xz3biqwcmw64qizxie/Tower key for megatests"
from_op AWS_ACCESS_KEY_ID="op://Dev/AWS megatests/username"
from_op AWS_SECRET_ACCESS_KEY="op://Dev/AWS megatests/password"
from_op GITHUB_TOKEN="op://Dev/GitHub nf-core PA Token Pulumi/token"
from_op OP_SERVICE_ACCOUNT_TOKEN="op://Employee/doroenisttgrfcmzihhunyizg4/credential"
```

## Development Guidelines

### When Working with This Project

1. **Always use `direnv exec .`** when running Pulumi commands to ensure AWS credentials are loaded
2. **Never commit secrets** - all credentials come from 1Password
3. **Test with preview** before deploying: `direnv exec . uv run pulumi preview`
4. **Check outputs** after deployment: `direnv exec . uv run pulumi stack output`

### Common Issues and Solutions

**"No valid credential sources found"**
- Solution: Use `direnv exec . uv run pulumi <command>`
- Root cause: AWS credentials not loaded from .envrc

**"static credentials are empty"**
- Solution: Check 1Password service account token is set in Pulumi config
- Command: `direnv exec . uv run pulumi config set --secret pulumi-onepassword:service_account_token "$OP_SERVICE_ACCOUNT_TOKEN"`

**Protected resource errors**
- Solution: Unprotect then delete from state: `pulumi state unprotect <urn>` then `pulumi state delete <urn>`
- Note: This removes from Pulumi state without affecting actual cloud resources

### Code Patterns

**1Password Secret Retrieval:**
```python
# Get secret from 1Password
secret_item = onepassword.get_item_output(
    vault="Dev",
    uuid="zwsrkl26xz3biqwcmw64qizxie",
    opts=pulumi.InvokeOptions(provider=onepassword_provider),
)
secret_value = secret_item.credential
```

**GitHub Secret Deployment:**
```python
github_secret = github.ActionsOrganizationSecret(
    "secret-name",
    secret_name="SECRET_NAME",
    plaintext_value=secret_value,
    visibility="all",
    opts=pulumi.ResourceOptions(provider=github_provider),
)
```

**Seqerakit Command Integration:**
```python
deploy_command = command.local.Command(
    "deploy-environment",
    create="seqerakit seqerakit/config.yml",
    environment={
        "TOWER_ACCESS_TOKEN": tower_token,
        **environment_vars,
    },
)
```

## Seqerakit Integration

The project uses seqerakit to deploy Seqera Platform compute environments:

- **Configuration**: Located in `seqerakit/` directory
- **Deployment**: Managed through Pulumi command provider
- **Environment IDs**: Extracted from seqerakit output and deployed to GitHub secrets
- **Features**: All environments have fusion snapshots enabled

See `seqerakit/README.md` and `seqerakit/CLAUDE.md` for detailed seqerakit-specific information.

## Outputs and Monitoring

The stack provides several outputs for monitoring and integration:

- `megatests_bucket`: S3 bucket information
- `compute_env_ids`: Seqera compute environment IDs
- `workspace_id`: Seqera workspace ID
- `github_secrets`: Names of deployed GitHub secrets

## Security Considerations

- **1Password Integration**: All secrets stored in 1Password, never in code
- **Service Account**: Uses dedicated 1Password service account for automation
- **GitHub Permissions**: Organization-level secrets with appropriate access control
- **AWS IAM**: Compute environments use dedicated service roles with least privilege

## Related Documentation

- **Main README**: `README.md` - User-facing project documentation
- **Seqerakit README**: `seqerakit/README.md` - Compute environment configurations
- **Seqerakit Context**: `seqerakit/CLAUDE.md` - Seqerakit-specific Claude context