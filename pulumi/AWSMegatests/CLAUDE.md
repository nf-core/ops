# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Pulumi project for AWS infrastructure management supporting nf-core megatests. The project combines:

1. **Pulumi Infrastructure**: Python-based infrastructure as code using Pulumi AWS provider
2. **Seqerakit Integration**: Tools for managing Nextflow Tower/Seqera Platform compute environments

## Common Development Commands

### Environment Setup

```bash
# Install dependencies using uv
uv sync

# Run commands in the uv environment
uv run <command>
```

### Pulumi Operations

```bash
# Preview infrastructure changes
uv run pulumi preview

# Deploy infrastructure
uv run pulumi up

# Destroy infrastructure
uv run pulumi destroy

# View current stack state
uv run pulumi stack

# Export stack outputs
uv run pulumi stack output
```

### Seqerakit Operations

```bash
# Set up environment variables
source seqerakit/vars.sh

# Deploy compute environments (after setting TOWER_ACCESS_TOKEN)
seqerakit compute-envs/aws_ireland_fusionv2_nvme_cpu.yml
seqerakit compute-envs/aws_ireland_fusionv2_nvme_gpu.yml
seqerakit compute-envs/aws_ireland_fusionv2_nvme_arm.yml
seqerakit compute-envs/aws_ireland_nofusion.yml
```

## Architecture

### Core Components

- **`__main__.py`**: Main Pulumi program defining AWS resources (currently creates an S3 bucket)
- **`seqerakit/`**: Contains Seqera Platform compute environment configurations
- **`seqerakit/vars.sh`**: Environment variables for seqerakit operations
- **`seqerakit/compute-envs/`**: YAML configurations for different AWS Batch compute environments

### Seqerakit Compute Environments

The project defines multiple compute environment configurations:

1. **CPU Environment** (`aws_ireland_fusionv2_nvme_cpu.yml`):

   - AWS Batch with Fusion v2 and NVMe storage
   - Instance types: c6id, m6id, r6id
   - Max CPUs: 500
   - SPOT provisioning model

2. **GPU Environment** (`aws_ireland_fusionv2_nvme_gpu.yml`):

   - Similar to CPU but with GPU-enabled instances

3. **ARM Environment** (`aws_ireland_fusionv2_nvme_arm.yml`):

   - ARM-based compute instances

4. **No Fusion Environment** (`aws_ireland_nofusion.yml`):
   - Traditional setup without Fusion v2

### Environment Variables

Key environment variables defined in `seqerakit/vars.sh`:

- `ORGANIZATION_NAME`: "nf-core"
- `WORKSPACE_NAME`: "AWSmegatests"
- `AWS_CREDENTIALS_NAME`: "tower-awstest"
- `AWS_REGION`: "eu-west-1"
- `AWS_WORK_DIR`: "s3://nf-core-awsmegatests"
- `AWS_COMPUTE_ENV_ALLOWED_BUCKETS`: S3 buckets for genomics data access

## Dependencies

- **Python**: >=3.12
- **Pulumi**: >=3.173.0, <4.0.0
- **Pulumi AWS Provider**: >=6.81.0, <7.0.0
- **UV**: Used for dependency management
- **Seqerakit**: External tool for Seqera Platform management

## Known Issues/Blockers

From the seqerakit README:

- How to enable snapshots with seqerakit
- How to create GPU-enabled compute environments with seqerakit

## Development Notes

- The project uses `uv` for Python dependency management instead of pip
- Pulumi state management uses the default backend
- All compute environments are configured for the `eu-west-1` region
- The infrastructure supports both SPOT and on-demand provisioning models
