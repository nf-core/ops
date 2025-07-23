# AWS Megatests - Pulumi Infrastructure

This repository manages AWS infrastructure for nf-core megatests using Pulumi Infrastructure as Code, integrating seqerakit compute environment deployment with automated GitHub secrets management.

## Overview

The AWS Megatests project provides:

- **S3 Bucket**: Imported and managed `nf-core-awsmegatests` bucket for workflow data
- **Compute Environments**: Three AWS Batch environments (CPU, ARM, GPU) deployed via seqerakit
- **GitHub Secrets**: Automated deployment of compute environment IDs and credentials to GitHub
- **1Password Integration**: Secure credential management using the Pulumi 1Password provider

## Quick Start

### Prerequisites

```bash
# Install dependencies
uv sync
brew install direnv

# Allow environment variables
direnv allow

# Login to Pulumi
pulumi login
```

### Deployment

```bash
# Preview infrastructure changes
direnv exec . uv run pulumi preview

# Deploy infrastructure
direnv exec . uv run pulumi up

# View current stack outputs
direnv exec . uv run pulumi stack output
```

## Architecture

### Infrastructure Components

#### S3 Storage

- **Bucket**: `nf-core-awsmegatests` (imported from existing AWS resources)
- **Region**: eu-west-1
- **Purpose**: Primary work directory and data storage for workflows

#### Compute Environments

Three AWS Batch compute environments managed through seqerakit:

1. **CPU Environment** (`aws_ireland_fusionv2_nvme_cpu`)
   - **Instance Types**: c6id, m6id, r6id (Intel x86_64)
   - **Max CPUs**: 500
   - **Features**: Fusion v2, Wave, NVMe storage, snapshots enabled

2. **ARM Environment** (`aws_ireland_fusionv2_nvme_cpu_ARM_snapshots`)
   - **Instance Types**: m6gd, r6gd, c6gd (ARM Graviton)
   - **Max CPUs**: 1000
   - **Features**: Fusion v2, Wave, NVMe storage, snapshots enabled

3. **GPU Environment** (`aws_ireland_fusionv2_nvme_gpu_snapshots`)
   - **Instance Types**: g4dn, g5 (GPU) + c6id, m6id, r6id (CPU)
   - **Max CPUs**: 500
   - **Features**: GPU enabled, Fusion v2, Wave, NVMe storage, snapshots enabled

#### GitHub Secrets

Automatically deployed GitHub organization secrets:

- `TOWER_ACCESS_TOKEN`: Seqera Platform access token
- `TOWER_WORKSPACE_ID`: Workspace ID for AWSmegatests
- `TOWER_COMPUTE_ENV_CPU`: CPU compute environment ID
- `TOWER_COMPUTE_ENV_ARM`: ARM compute environment ID
- `TOWER_COMPUTE_ENV_GPU`: GPU compute environment ID

### Technology Stack

- **Infrastructure**: Pulumi with Python
- **Cloud Provider**: AWS (eu-west-1)
- **Compute**: AWS Batch with SPOT instances
- **Storage**: S3 + NVMe local storage
- **Container Platform**: Docker with Wave optimization
- **Secrets Management**: 1Password with Pulumi provider
- **CI/CD**: GitHub Actions with automated secret deployment

## Configuration

### Environment Variables (.envrc)

```bash
# Organization settings
export ORGANIZATION_NAME="nf-core"
export WORKSPACE_NAME="AWSmegatests"
export AWS_REGION="eu-west-1"

# AWS configuration
export AWS_WORK_DIR="s3://nf-core-awsmegatests"
export AWS_CREDENTIALS_NAME="tower-awstest"
export AWS_COMPUTE_ENV_ALLOWED_BUCKETS="s3://ngi-igenomes,s3://annotation-cache"

# 1Password secret references
from_op TOWER_ACCESS_TOKEN="op://Dev/zwsrkl26xz3biqwcmw64qizxie/Tower key for megatests"
from_op AWS_ACCESS_KEY_ID="op://Dev/AWS megatests/username"
from_op AWS_SECRET_ACCESS_KEY="op://Dev/AWS megatests/password"
from_op GITHUB_TOKEN="op://Dev/GitHub nf-core PA Token Pulumi/token"
from_op OP_SERVICE_ACCOUNT_TOKEN="op://Employee/doroenisttgrfcmzihhunyizg4/credential"
```

### Pulumi Configuration

```bash
# Set 1Password service account token
direnv exec . uv run pulumi config set --secret pulumi-onepassword:service_account_token "$OP_SERVICE_ACCOUNT_TOKEN"
```

## Seqerakit Integration

The project uses seqerakit for compute environment deployment through Pulumi's command provider:

```python
# Seqerakit deployment commands
deploy_cpu = command.local.Command("deploy-cpu-environment",
    create="seqerakit seqerakit/aws_ireland_fusionv2_nvme_cpu_current.yml")

deploy_arm = command.local.Command("deploy-arm-environment",
    create="seqerakit seqerakit/aws_ireland_fusionv2_nvme_cpu_arm_current.yml")

deploy_gpu = command.local.Command("deploy-gpu-environment",
    create="seqerakit seqerakit/aws_ireland_fusionv2_nvme_gpu_current.yml")
```

### Seqerakit Configurations

Located in `seqerakit/` directory:

- **YAML configs**: Reference JSON configurations with metadata
- **JSON configs**: Complete compute environment specifications
- **Features**: All environments have fusion snapshots enabled

See [seqerakit/README.md](seqerakit/README.md) for detailed configuration information.

## Outputs

The Pulumi stack provides these outputs:

```bash
# View all outputs
direnv exec . uv run pulumi stack output

# Specific outputs
direnv exec . uv run pulumi stack output megatests_bucket    # S3 bucket info
direnv exec . uv run pulumi stack output compute_env_ids    # Environment IDs
direnv exec . uv run pulumi stack output workspace_id      # Seqera workspace ID
direnv exec . uv run pulumi stack output github_secrets    # Secret names
```

## Development Workflow

### For Contributors

**📝 Contributing to Infrastructure**

Contributors **do not need** to run infrastructure locally. The workflow is:

1. **Make your changes** to seqerakit configurations in `seqerakit/` directory
2. **Create a Pull Request** with your changes
3. **Core team will review** and run `pulumi preview` in Pulumi Cloud
4. **Infrastructure is deployed** automatically via Pulumi Cloud + 1Password integration

**Requirements for Contributors:**

- ✅ None! No 1Password, AWS, or Pulumi access needed
- ✅ Just edit the configuration files and make a PR
- ✅ Core team handles all infrastructure operations

### For Core Team (Infrastructure Access)

**🔧 Infrastructure Management**

Core team members with 1Password and Pulumi access:

1. **Setup credentials**: Ensure 1Password service account token is configured
2. **Preview changes**: Review PR changes in Pulumi Cloud preview
3. **Deploy**: Merge PR triggers automatic deployment via Pulumi Cloud
4. **Monitor**: Check Pulumi Console and AWS Console for deployment status

**Local Development (Optional):**

```bash
# If you need to run locally (requires 1Password access)
direnv allow
direnv exec . uv run pulumi preview
direnv exec . uv run pulumi up
```

### Debugging Features

**🔍 Enhanced Debugging**

The system includes detailed debugging output:

- **Tower CLI Availability**: Checks if Tower CLI is installed and accessible
- **Authentication Status**: Verifies Tower CLI can authenticate with Seqera Platform
- **Environment Listing**: Shows available compute environments for troubleshooting
- **ID Extraction**: Detailed logging of compute environment ID retrieval process

### Common Operations (Core Team)

```bash
# View current state
uv run pulumi stack output

# Refresh state to match actual infrastructure
uv run pulumi refresh

# View infrastructure in Pulumi Console
uv run pulumi console

# Debug failed deployments
uv run pulumi logs

# Import existing AWS resources (if needed)
uv run pulumi import aws:s3/bucket:Bucket nf-core-awsmegatests nf-core-awsmegatests
```

### Troubleshooting

**"No valid credential sources found"**

- Run commands with `direnv exec .` to load AWS credentials
- Ensure `.envrc` is allowed: `direnv allow`

**"static credentials are empty"**

- Check 1Password service account token: `echo $OP_SERVICE_ACCOUNT_TOKEN`
- Verify 1Password items exist and are accessible

**Protected resource errors**

- Unprotect resources: `uv run pulumi state unprotect <urn>`
- Remove from state: `uv run pulumi state delete <urn>`

## Security

### Credential Management

- **1Password Integration**: All secrets stored in 1Password vaults
- **Service Account**: Uses 1Password service account for automated access
- **GitHub Secrets**: Automatically deployed for CI/CD workflows
- **No Hardcoded Secrets**: All credentials loaded from secure sources

### Access Control

- **AWS IAM**: Compute environments use dedicated service roles
- **Seqera Platform**: Token-based authentication with workspace isolation
- **GitHub**: Organization-level secrets with appropriate permissions

## Monitoring and Observability

- **Pulumi Console**: Infrastructure state and history
- **AWS Console**: Compute environment and job monitoring
- **Seqera Platform**: Workflow execution and resource usage
- **GitHub Actions**: Deployment logs and status

## Related Projects

- **nf-core**: Main nf-core project repository
- **nf-core/test-datasets**: Test data and validation workflows
- **Seqera Platform**: Workflow execution and monitoring platform

## Support

For issues related to:

- **Infrastructure**: Check Pulumi logs and AWS console
- **Compute Environments**: Review seqerakit configurations and Seqera Platform
- **Secrets Management**: Verify 1Password integration and GitHub permissions
