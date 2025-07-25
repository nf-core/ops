# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This directory contains seqerakit configurations for nf-core megatest infrastructure on the Seqera Platform, integrated with the parent Pulumi AWSMegatests project. Seqerakit is a Python-based Infrastructure as Code (IaC) utility that uses YAML configurations to automate Seqera Platform resource creation and management.

**Integration**: These seqerakit configurations are deployed through the parent Pulumi project using the command provider, which automatically extracts compute environment IDs and deploys them as GitHub secrets.

## Common Commands

### Prerequisites

**Note**: These configurations are typically deployed through the parent Pulumi project, not directly via seqerakit commands.

For standalone usage:
```bash
# Install seqerakit
pip install seqerakit

# Install direnv (for 1Password integration)
brew install direnv

# Allow the .envrc file (loads secrets from 1Password) 
cd .. && direnv allow

# Alternatively, manually load environment variables
# export TOWER_ACCESS_TOKEN=<your-token>
```

### Seqerakit Operations

**Recommended**: Use the parent Pulumi project for deployment:
```bash
# From parent directory
cd .. && direnv exec . uv run pulumi up
```

**Direct seqerakit usage** (for testing/debugging):
```bash
# Dry run to validate configuration
seqerakit aws_ireland_fusionv2_nvme_cpu_current.yml --dryrun

# Deploy individual compute environments (current production configs)
seqerakit aws_ireland_fusionv2_nvme_cpu_current.yml
seqerakit aws_ireland_fusionv2_nvme_cpu_arm_current.yml
seqerakit aws_ireland_fusionv2_nvme_gpu_current.yml

# Delete resources
seqerakit aws_ireland_fusionv2_nvme_cpu_current.yml --delete
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

The `.envrc` file defines key configuration variables and loads secrets from 1Password:

**Static Configuration**:

- `ORGANIZATION_NAME`: "nf-core"
- `WORKSPACE_NAME`: "AWSmegatests"
- `AWS_CREDENTIALS_NAME`: "tower-awstest"
- `AWS_REGION`: "eu-west-1"
- `AWS_WORK_DIR`: "s3://nf-core-awsmegatests"
- `AWS_COMPUTE_ENV_ALLOWED_BUCKETS`: "s3://ngi-igenomes,s3://annotation-cache"

**1Password Secrets**:

- `TOWER_ACCESS_TOKEN`: `op://Dev/Tower nf-core Access Token/password`
- `AWS_ACCESS_KEY_ID`: `op://Dev/AWS Tower Test Credentials/access key id`
- `AWS_SECRET_ACCESS_KEY`: `op://Dev/AWS Tower Test Credentials/secret access key`

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

1. **Environment Setup**: `direnv allow` to load configuration variables and 1Password secrets
2. **Validation**: Use `--dryrun` flag to validate YAML configurations
3. **Deployment**: Execute seqerakit commands to create compute environments
4. **Management**: Use `--delete` flag to remove resources when needed

## Pulumi Integration

### How Seqerakit Integrates with Pulumi

These seqerakit configurations are deployed through the parent Pulumi project using:

1. **Command Provider**: Executes seqerakit CLI commands as Pulumi resources
2. **Output Extraction**: Parses seqerakit output to extract compute environment IDs  
3. **GitHub Secrets**: Automatically deploys extracted IDs as GitHub organization secrets
4. **1Password Integration**: Inherits secure credential management from parent project

### Current Infrastructure Files

- `current-env-cpu.json`: Exported CPU environment configuration
- `current-env-cpu-arm.json`: Exported CPU ARM environment configuration
- `current-env-gpu.json`: Exported GPU environment configuration
- `aws_ireland_fusionv2_nvme_cpu_current.yml`: Seqerakit config for CPU environment
- `aws_ireland_fusionv2_nvme_cpu_arm_current.yml`: Seqerakit config for CPU ARM environment
- `aws_ireland_fusionv2_nvme_gpu_current.yml`: Seqerakit config for GPU environment

### Deployment Process

1. **Pulumi Command Resources**: Execute seqerakit deployment commands
2. **ID Extraction**: Parse seqerakit output to get compute environment IDs
3. **GitHub Secrets**: Deploy extracted IDs to GitHub organization secrets
4. **Workspace ID**: Extract and deploy Seqera workspace ID

### Required Configuration

Environment variables are inherited from the parent `.envrc`:
- `TOWER_ACCESS_TOKEN`: Seqera Platform access token (from 1Password)
- `ORGANIZATION_NAME`, `WORKSPACE_NAME`: Seqera Platform identifiers
- AWS credentials for compute environment deployment

### Migration from Manual Setup

The current configurations were exported from existing environments:

- CPU: `53ljSqphNKjm6jjmuB6T9b` → `aws_ireland_fusionv2_nvme_cpu`
- CPU ARM: `5LWYX9a2GxrIFiax8tn9DV` → `aws_ireland_fusionv2_nvme_cpu_ARM_snapshots`
- GPU: `7Gjp4zOBlhH9xMIlfs9LM2` → `aws_ireland_fusionv2_nvme_gpu_snapshots`

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
