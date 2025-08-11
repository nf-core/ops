# AWS Megatests - Claude Code Context

This file provides Claude Code with context for the AWS Megatests Pulumi infrastructure project.

## Project Overview

This is a **Pulumi Infrastructure as Code (IaC) project** that manages AWS infrastructure for nf-core megatests. The project integrates multiple technologies:

- **Pulumi**: Python-based infrastructure as code
- **Seqera Terraform Provider**: Native Terraform provider integration for Seqera Platform
- **Pulumi ESC**: Environment management and secret storage
- **GitHub**: Automated variable and secret deployment for CI/CD workflows

## Architecture

### Core Components

1. **S3 Bucket Management**
   - Imports existing `nf-core-awsmegatests` bucket
   - Manages bucket configuration through Pulumi

2. **Seqera Compute Environments**
   - Three AWS Batch environments: CPU, ARM, GPU
   - Deployed via native Seqera Terraform provider
   - All environments have fusion snapshots enabled

3. **GitHub Integration**
   - Automatically pushes compute environment IDs to GitHub organization variables
   - Manages Seqera Platform access tokens for CI/CD

4. **Pulumi ESC Integration**
   - Secure credential management using Pulumi ESC environments
   - AWS and GitHub credentials from ESC

### File Structure

```
AWSMegatests/
├── __main__.py                 # Main Pulumi program
├── seqera_terraform.py         # Seqera Terraform provider integration
├── s3_infrastructure.py        # S3 bucket management
├── towerforge_credentials.py   # AWS IAM credentials for TowerForge
├── github_integration.py       # GitHub variables and secrets
├── providers.py                # Provider configurations
├── secrets_manager.py          # ESC configuration management
├── requirements.txt            # Python dependencies
├── Pulumi.yaml                # Pulumi project configuration
├── README.md                  # Project documentation
├── CLAUDE.md                  # This file - Claude context
├── sdks/seqera/               # Auto-generated Seqera SDK
└── seqerakit/                 # Configuration files (read-only)
    ├── *.yml                  # Seqerakit YAML configurations (for reference)
    └── *.json                 # Compute environment JSON specs (used by Terraform provider)
```

## Common Commands

### Prerequisites

```bash
# Install UV and dependencies
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync

# Login to Pulumi
pulumi login

# Ensure Pulumi ESC environment is properly configured
pulumi env ls
```

### Development Workflow

```bash
# Preview changes
uv run pulumi preview

# Deploy infrastructure
uv run pulumi up

# View outputs
uv run pulumi stack output

# Refresh state to match actual infrastructure
uv run pulumi refresh
```

### State Management

```bash
# List stack resources
uv run pulumi stack --show-urns

# Unprotect resources
uv run pulumi state unprotect <urn>

# Remove resources from state (without deleting from cloud)
uv run pulumi state delete <urn>

# Protect critical resources
uv run pulumi state protect <urn>
```

## Key Technologies

### Pulumi Providers Used

1. **AWS Provider** (`pulumi-aws`)
   - Manages S3 bucket and IAM resources
   - Uses ESC-provided AWS credentials

2. **Seqera Terraform Provider** (`pulumi-seqera`)
   - Native Terraform provider for Seqera Platform
   - Manages compute environments directly

3. **GitHub Provider** (`pulumi-github`)
   - Manages organization variables and secrets
   - Uses ESC-provided GitHub token

### Environment Configuration

The project uses **Pulumi ESC** for all configuration and secrets:

- **AWS credentials**: Provided by ESC environment
- **Seqera Platform tokens**: Stored in ESC
- **GitHub tokens**: Managed through ESC
- **Workspace configuration**: Defined in ESC environment

## Development Guidelines

### When Working with This Project

1. **Use standard Pulumi commands** - ESC handles credential loading automatically
2. **Never commit secrets** - all credentials managed through Pulumi ESC
3. **Test with preview** before deploying: `uv run pulumi preview`
4. **Check outputs** after deployment: `uv run pulumi stack output`

### Common Issues and Solutions

**"No valid credential sources found"**
- Solution: Ensure Pulumi ESC environment is properly configured
- Check: `pulumi env ls` and `pulumi env open <env-name>`

**"Provider configuration error"**
- Solution: Verify ESC environment contains required credentials
- Check: ESC environment has `aws`, `seqera`, and `github` provider configurations

**Protected resource errors**
- Solution: Unprotect then delete from state: `pulumi state unprotect <urn>` then `pulumi state delete <urn>`
- Note: This removes from Pulumi state without affecting actual cloud resources

### Code Patterns

**Seqera Terraform Provider Usage:**
```python
# Create Seqera provider
provider = seqera.Provider(
    "seqera-provider",
    bearer_auth=config["tower_access_token"],
    server_url="https://api.cloud.seqera.io",
)

# Create compute environment
compute_env = seqera.ComputeEnv(
    "environment-name",
    compute_env=compute_env_args,
    workspace_id=workspace_id,
    opts=pulumi.ResourceOptions(provider=provider)
)
```

**GitHub Variable Deployment:**
```python
github_variable = github.ActionsOrganizationVariable(
    "variable-name",
    variable_name="VARIABLE_NAME", 
    value=variable_value,
    visibility="all",
    opts=pulumi.ResourceOptions(provider=github_provider),
)
```

## Seqera Integration

The project uses the native Seqera Terraform provider for compute environment management:

- **Configuration**: Reads existing seqerakit JSON files for compute environment specifications
- **Deployment**: Uses native Terraform provider resources instead of CLI commands
- **Environment IDs**: Direct access to compute environment IDs as resource outputs
- **Features**: All environments have fusion snapshots enabled

The `seqerakit/` directory contains configuration files that are read by the Terraform provider integration but are not actively used for deployment.

## Outputs and Monitoring

The stack provides several outputs for monitoring and integration:

- `megatests_bucket`: S3 bucket information
- `compute_env_ids`: Seqera compute environment IDs
- `workspace_id`: Seqera workspace ID
- `terraform_resources`: Terraform provider resource information
- `github_resources`: GitHub integration status

## Security Considerations

- **Pulumi ESC Integration**: All secrets managed through Pulumi ESC environments
- **Provider Security**: Native Terraform provider with proper authentication
- **GitHub Permissions**: Organization-level variables with appropriate access control
- **AWS IAM**: Compute environments use dedicated TowerForge service roles with least privilege

## Related Documentation

- **Main README**: `README.md` - User-facing project documentation
- **Seqerakit Configs**: `seqerakit/README.md` - Configuration reference (read-only)