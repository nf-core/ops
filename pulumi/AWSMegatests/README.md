# AWS Megatests - OpenTofu Infrastructure

Manages AWS infrastructure for nf-core megatests using OpenTofu, integrating Seqera Platform compute environments with automated GitHub variable management.

## Overview

- **S3 Bucket**: Imported `nf-core-awsmegatests` bucket with lifecycle rules
- **Compute Environments**: Three AWS Batch environments (CPU, ARM, GPU) via Seqera Terraform provider
- **GitHub Variables**: Automated deployment of compute environment IDs to GitHub org variables
- **Workspace Participants**: Automated nf-core team member management in Seqera Platform
- **1Password Integration**: Secrets from 1Password via the Terraform provider

## Quick Start

```bash
# Install OpenTofu
brew install opentofu

# Initialize providers
tofu init

# Preview changes
tofu plan

# Deploy
tofu apply
```

## Architecture

### Compute Environments

| Environment | Instance Types | Max CPUs | Features |
|---|---|---|---|
| CPU | c6id, m6id, r6id | 1000 | Fusion v2, Wave, NVMe, Snapshots |
| GPU | g4dn, g5, c6id, m6id, r6id | 500 | GPU, Fusion v2, Wave, NVMe, Snapshots |
| ARM | m6gd, r6gd, c6gd | 500 | ARM64, Fusion v2, Wave, NVMe, Snapshots |

### GitHub Organization Variables

- `TOWER_COMPUTE_ENV_CPU` / `TOWER_COMPUTE_ENV_GPU` / `TOWER_COMPUTE_ENV_ARM`
- `TOWER_WORKSPACE_ID`
- `AWS_S3_BUCKET`

### Secrets Management

All secrets come from 1Password via the `onepassword` provider:
- Seqera Platform token
- GitHub tokens
- AWS credentials (for IAM user access keys)

## File Structure

```
AWSMegatests/
├── versions.tf              # Provider version constraints
├── providers.tf             # Provider configurations
├── variables.tf             # Input variables
├── onepassword.tf           # 1Password data sources
├── locals.tf                # Nextflow config merging + shared defaults
├── s3.tf                    # S3 bucket + lifecycle + CORS
├── iam.tf                   # IAM user, policies, access keys
├── seqera_credentials.tf    # Seqera AWS credential
├── github_credential.tf     # Seqera GitHub credential
├── compute_environments.tf  # 3 Seqera compute environments
├── github.tf                # GitHub org variables
├── participants.tf          # Workspace participant management
├── outputs.tf               # Stack outputs
├── configs/                 # Nextflow config files
└── scripts/                 # Team management scripts
```

## Common Commands

```bash
tofu init          # Initialize providers
tofu plan          # Preview changes
tofu apply         # Deploy infrastructure
tofu output        # View outputs
tofu fmt -check    # Check formatting
```

## Contributing

Contributors don't need infrastructure access. Edit configs in `configs/` and open a PR. Core team handles deployment.
