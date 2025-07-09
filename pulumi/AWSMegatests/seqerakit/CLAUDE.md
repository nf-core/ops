# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a seqerakit configuration repository for automating the setup of nf-core megatest infrastructure on the Seqera Platform. Seqerakit is a Python-based Infrastructure as Code (IaC) utility that uses YAML configurations to automate Seqera Platform resource creation and management.

## Common Commands

### Prerequisites
```bash
# Install seqerakit
pip install seqerakit

# Set platform access token
export TOWER_ACCESS_TOKEN=<your-token>

# Load environment variables
source vars.sh
```

### Seqerakit Operations
```bash
# Dry run to validate configuration
seqerakit compute-envs/aws_ireland_fusionv2_nvme_cpu.yml --dryrun

# Deploy individual compute environments
seqerakit compute-envs/aws_ireland_fusionv2_nvme_cpu.yml
seqerakit compute-envs/aws_ireland_fusionv2_nvme_gpu.yml
seqerakit compute-envs/aws_ireland_fusionv2_nvme_arm.yml
seqerakit compute-envs/aws_ireland_nofusion.yml

# Deploy all compute environments
seqerakit compute-envs/*.yml

# Delete resources
seqerakit compute-envs/aws_ireland_fusionv2_nvme_cpu.yml --delete
```

## Architecture

### Configuration Structure

The repository contains YAML-based Infrastructure as Code configurations for four distinct AWS Batch compute environments:

1. **CPU Environment** (`aws_ireland_fusionv2_nvme_cpu.yml`):
   - Instance types: c6id, m6id, r6id (Intel x86_64 with NVMe storage)
   - Features: Fusion v2, Wave, fast storage, no EBS auto-scale
   - Provisioning: SPOT instances

2. **GPU Environment** (`aws_ireland_fusionv2_nvme_gpu.yml`):
   - Instance types: g4dn, g5, c6id, m6id, r6id (GPU + CPU instances)
   - Features: GPU enabled, Fusion v2, Wave, fast storage
   - Provisioning: SPOT instances

3. **ARM Environment** (`aws_ireland_fusionv2_nvme_arm.yml`):
   - Instance types: m6gd, c6gd, r6gd (ARM Graviton2 with NVMe storage)
   - Features: Fusion v2, Wave, fast storage
   - Provisioning: SPOT instances

4. **No Fusion Environment** (`aws_ireland_nofusion.yml`):
   - Traditional setup without Fusion v2 optimizations
   - Features: Wave disabled, standard EBS storage
   - Provisioning: SPOT instances

### Environment Variables

The `vars.sh` file defines key configuration variables:

- `ORGANIZATION_NAME`: "nf-core"
- `WORKSPACE_NAME`: "AWSmegatests"
- `AWS_CREDENTIALS_NAME`: "tower-awstest"
- `AWS_REGION`: "eu-west-1"
- `AWS_WORK_DIR`: "s3://nf-core-awsmegatests"
- `AWS_COMPUTE_ENV_ALLOWED_BUCKETS`: "s3://ngi-igenomes,s3://annotation-cache"

### Common Configuration Patterns

All compute environments share:
- **Type**: aws-batch
- **Config Mode**: forge
- **Max CPUs**: 500
- **Wait State**: AVAILABLE
- **On Exists**: overwrite
- **Provisioning Model**: SPOT

Key differentiators:
- **Instance Types**: Vary by architecture (x86_64, ARM, GPU)
- **Fusion v2**: Enabled for performance environments, disabled for traditional
- **Fast Storage**: NVMe-enabled instances vs standard storage
- **GPU Support**: Only enabled for GPU environment

## Workflow

The typical deployment workflow:

1. **Environment Setup**: Source `vars.sh` to load configuration variables
2. **Validation**: Use `--dryrun` flag to validate YAML configurations
3. **Deployment**: Execute seqerakit commands to create compute environments
4. **Management**: Use `--delete` flag to remove resources when needed

## Known Issues

From the project README:
- How to enable snapshots with seqerakit
- How to create GPU-enabled compute environments with seqerakit (partially addressed in current configs)

## Technical Details

- **Cloud Provider**: AWS
- **Region**: eu-west-1 (Ireland)
- **Compute Backend**: AWS Batch
- **Container Technology**: Docker with Wave optimization
- **Storage**: S3 for work directory and data buckets
- **Networking**: Managed by Seqera Platform forge mode
- **Cost Optimization**: SPOT instances for all environments