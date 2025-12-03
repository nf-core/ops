# Resource Optimization Workspace

Seqera Platform workspace for resource optimization testing and analysis.

## Overview

This workspace provides a focused testing environment for analyzing and optimizing pipeline resource requirements. It includes:

- **CPU-Only Compute Environment**: Single compute environment for resource profiling
- **S3 Storage**: Dedicated bucket for test results
- **Minimal Configuration**: Streamlined setup for resource analysis
- **TowerForge Credentials**: IAM user and policies for compute environment access

Unlike the full AWS Megatests workspace, this workspace intentionally omits GPU and ARM compute environments to focus specifically on CPU resource optimization work.

## Configuration

The workspace configuration is defined in `workspace_config.py`:

- **Workspace Name**: ResourceOptimization
- **Organization**: nf-core
- **AWS Region**: eu-west-1
- **S3 Bucket**: nf-core-resource-optimization

### Compute Environments

1. **CPU Environment** (Only)
   - Instance types: c6id, m6id, r6id
   - Max CPUs: 500
   - Fusion v2 with NVMe storage
   - SPOT provisioning model

**Note**: GPU and ARM environments are explicitly disabled for this workspace.

## Deployment

### Prerequisites

1. Python 3.12+
2. uv package manager
3. Pulumi CLI
4. AWS credentials
5. Seqera Platform access token

### Initial Setup

```bash
# Install dependencies
uv sync

# Login to Pulumi
pulumi login

# Create a new stack
pulumi stack init prod

# Configure ESC environment
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

- `workspace`: Workspace details (name, organization, ID, description)
- `s3_bucket`: S3 bucket information
- `compute_env_ids`: IDs of compute environment (CPU only)
- `terraform_resources`: CPU compute environment ID
- `workspace_participants`: Team member sync status (if enabled)

**Note**: GitHub integration outputs are omitted as GitHub integration is disabled by default.

## Structure

```
resource_optimization/
├── __main__.py              # Main Pulumi program
├── workspace_config.py      # Workspace-specific configuration
├── Pulumi.yaml             # Pulumi project definition
├── pyproject.toml          # Python dependencies
├── requirements.txt        # Alternative dependency specification
└── .gitignore             # Git ignore patterns
```

## Shared Modules

This workspace uses shared modules from `../shared/`:
- `providers/`: AWS, Seqera providers
- `infrastructure/`: S3, IAM, compute environments
- `config/`: Configuration management
- `utils/`: Helper functions

## Use Cases

This workspace is designed for:

1. **Resource Profiling**: Running pipelines with detailed resource monitoring
2. **Optimization Testing**: Testing resource requirement adjustments
3. **Cost Analysis**: Analyzing compute costs for different configurations
4. **Performance Benchmarking**: Comparing execution times across instance types

## Customization

### Enabling GitHub Integration

Edit `workspace_config.py`:

```python
"github_integration": {
    "enabled": True,  # Change from False
    "organization": "nf-core",
}
```

### Adjusting Compute Limits

Edit `workspace_config.py`:

```python
"compute_environments": {
    "cpu": {
        "enabled": True,
        "max_cpus": 1000,  # Increase from 500
        ...
    }
}
```

### Adding GPU or ARM Support

If resource optimization work expands to include GPU or ARM:

```python
"compute_environments": {
    "cpu": {...},
    "gpu": {
        "enabled": True,  # Change from False
        "name": "aws_ireland_fusionv2_nvme_gpu",
        "instance_types": ["g4dn", "g5"],
        "max_cpus": 500,
    },
}
```

## Maintenance

### Resource Monitoring

Monitor resource usage through:
1. Seqera Platform dashboard
2. CloudWatch metrics
3. S3 bucket analytics

### Cost Optimization

- Review instance type usage
- Adjust max_cpus based on actual usage
- Consider SPOT vs on-demand mix

## Troubleshooting

**Issue**: Import errors from shared modules
**Solution**: The `__main__.py` automatically adds `../shared` to the Python path. Ensure the shared directory exists.

**Issue**: Compute environment not deploying
**Solution**: Verify `TOWER_ACCESS_TOKEN` and workspace ID in ESC configuration.

**Issue**: S3 bucket creation fails
**Solution**: Check if bucket name is globally unique and region is correct.

## Related Documentation

- [Main Seqera Platform README](../README.md)
- [Shared Module Documentation](../shared/README.md)
- [AWS Megatests Workspace](../awsmegatests/README.md)
