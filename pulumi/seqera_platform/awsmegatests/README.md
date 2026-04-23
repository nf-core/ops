# AWS Megatests Workspace

Seqera Platform workspace for nf-core AWS megatests infrastructure.

## Overview

This workspace provides the complete testing infrastructure for nf-core pipelines on AWS, including:

- **Multiple Compute Environments**: CPU, GPU, and ARM instances
- **S3 Storage**: Dedicated bucket for test data and results
- **GitHub CI/CD Integration**: Automatic variable and secret management
- **Team Access**: Automated workspace participant management
- **TowerForge Credentials**: IAM user and policies for compute environment access

## Configuration

The workspace configuration is defined in `workspace_config.py`:

- **Workspace Name**: AWSmegatests
- **Organization**: nf-core
- **AWS Region**: eu-west-1
- **S3 Bucket**: nf-core-awsmegatests

### Compute Environments

1. **CPU Environment**
   - Instance types: c6id, m6id, r6id
   - Max CPUs: 500
   - Fusion v2 with NVMe storage

2. **GPU Environment**
   - Instance types: g4dn, g5
   - Max CPUs: 500
   - GPU-enabled for accelerated workloads

3. **ARM Environment**
   - Instance types: c6gd, m6gd, r6gd
   - Max CPUs: 500
   - ARM64 architecture testing

## Deployment

### Prerequisites

1. Python 3.12+
2. uv package manager
3. Pulumi CLI
4. AWS credentials
5. Seqera Platform access token
6. GitHub personal access token

### Initial Setup

```bash
# Install dependencies
uv sync

# Login to Pulumi
pulumi login

# Create a new stack (if needed)
pulumi stack init prod

# Configure ESC environment (if using)
# Edit Pulumi.<stack>.yaml to reference ESC environment
```

### Deploy Infrastructure

```bash
# Preview changes
uv run pulumi preview

# Deploy
uv run pulumi up

# View outputs
uv run pulumi stack output
```

## Outputs

The stack exports:

- `workspace`: Workspace details (name, organization, ID)
- `megatests_bucket`: S3 bucket information
- `compute_env_ids`: IDs of all compute environments
- `github_resources`: GitHub variables and secrets
- `github_credential`: Seqera Platform credential for GitHub access
- `terraform_resources`: Compute environment IDs by type
- `workspace_participants`: Team member sync status

## Structure

```
awsmegatests/
├── __main__.py              # Main Pulumi program
├── workspace_config.py      # Workspace-specific configuration
├── Pulumi.yaml             # Pulumi project definition
├── pyproject.toml          # Python dependencies
├── requirements.txt        # Alternative dependency specification
└── .gitignore             # Git ignore patterns
```

## Shared Modules

This workspace uses shared modules from `../shared/`:
- `providers/`: AWS, GitHub, Seqera providers
- `infrastructure/`: S3, IAM, compute environments
- `integrations/`: GitHub resources, credentials
- `config/`: Configuration management
- `utils/`: Helper functions

## Maintenance

### Updating Compute Environments

Edit `workspace_config.py` to modify compute environment settings:

```python
"compute_environments": {
    "cpu": {
        "enabled": True,  # Set to False to disable
        "max_cpus": 500,  # Adjust as needed
        ...
    }
}
```

Then run `pulumi up` to apply changes.

### Adding Team Members

Workspace participants are managed automatically via GitHub teams:
- `nf-core` team → OWNER role
- `nf-core-maintainers` team → MAINTAIN role

Team membership updates are synced on each deployment.

## Troubleshooting

**Issue**: Import errors from shared modules
**Solution**: The `__main__.py` automatically adds `../shared` to the Python path. Ensure the shared directory exists.

**Issue**: GitHub resources not creating
**Solution**: Check that `GITHUB_TOKEN` has appropriate permissions for organization variables and secrets.

**Issue**: Compute environments not deploying
**Solution**: Verify `TOWER_ACCESS_TOKEN` and workspace ID in ESC configuration.

## Related Documentation

- [Main Seqera Platform README](../README.md)
- [Shared Module Documentation](../shared/README.md)
- [Legacy AWSMegatests](../../AWSMegatests/CLAUDE.md)
