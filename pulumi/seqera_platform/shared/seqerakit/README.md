# nf-core megatest seqerakit

Contains the seqerakit configurations for the three core compute environments used in nf-core megatests on the Seqera Platform.

## Quick Start

1. Install seqerakit: `pip install seqerakit`
2. Install direnv: `brew install direnv`
3. Allow environment loading: `direnv allow`
4. Deploy compute environments:
   ```bash
   seqerakit aws_ireland_fusionv2_nvme_cpu_current.yml
   seqerakit aws_ireland_fusionv2_nvme_cpu_arm_current.yml
   seqerakit aws_ireland_fusionv2_nvme_gpu_current.yml
   ```

## Architecture

### Three Core Compute Environments

This repository manages **three compute environments** on AWS Batch, all with fusion snapshots enabled:

#### 1. **CPU Environment** (`aws_ireland_fusionv2_nvme_cpu`)

- **Instance Types**: `c6id`, `m6id`, `r6id` (Intel x86_64 with NVMe storage)
- **Features**: Fusion v2, Wave, NVMe storage, **snapshots enabled**
- **Provisioning**: SPOT instances
- **Max CPUs**: 500
- **Use Case**: Standard CPU-intensive workflows

#### 2. **ARM Environment** (`aws_ireland_fusionv2_nvme_cpu_ARM_snapshots`)

- **Instance Types**: `m6gd`, `r6gd`, `c6gd` (ARM Graviton with NVMe storage)
- **Features**: Fusion v2, Wave, NVMe storage, **snapshots enabled**
- **Provisioning**: SPOT instances
- **Max CPUs**: 1000
- **Use Case**: ARM-optimized workflows and cost optimization

#### 3. **GPU Environment** (`aws_ireland_fusionv2_nvme_gpu_snapshots`)

- **Instance Types**: `g4dn`, `g5` (GPU) + `c6id`, `m6id`, `r6id` (CPU fallback)
- **Features**: GPU enabled, Fusion v2, Wave, NVMe storage, **snapshots enabled**
- **Provisioning**: SPOT instances
- **Max CPUs**: 500
- **Use Case**: GPU-accelerated workflows (ML, bioinformatics tools)

### Common Configuration

All environments share these settings:

- **Type**: aws-batch
- **Region**: eu-west-1 (Ireland)
- **Provisioning**: SPOT instances
- **Wave**: Enabled for container optimization
- **Fusion v2**: Enabled for high-performance I/O
- **NVMe Storage**: Enabled for fast local storage
- **Snapshots**: **Enabled** for all environments
- **Wait State**: AVAILABLE
- **Overwrite**: Enabled

## Snapshots Configuration

All three environments have fusion snapshots enabled using the seqerakit `fusionSnapshots` field:

```json
{
  "fusionSnapshots": true,
  "fusion2Enabled": true,
  "waveEnabled": true,
  "nvnmeStorageEnabled": true,
  "nextflowConfig": "aws.batch.maxSpotAttempts=5\nprocess {\n    maxRetries = 2\n    errorStrategy = { task.exitStatus in ((130..145) + 104 + 175) ? 'retry' : 'terminate' }\n}\n"
}
```

This approach keeps snapshots configuration separate from Nextflow configuration, making it cleaner and more maintainable.

## Seqerakit Deployment

### Why Seqerakit?

We use seqerakit for Infrastructure as Code management of compute environments because:

- **Native snapshots support**: Supports the `fusionSnapshots` field directly
- **Clean configuration**: No need to embed snapshots in `nextflowConfig`
- **GitOps workflow**: Infrastructure managed through version control
- **Validation**: Built-in `--dryrun` support for testing configurations

### Deployment Commands

```bash
# Deploy individual environments
seqerakit aws_ireland_fusionv2_nvme_cpu_current.yml
seqerakit aws_ireland_fusionv2_nvme_cpu_arm_current.yml
seqerakit aws_ireland_fusionv2_nvme_gpu_current.yml

# Validate configurations (dry run)
seqerakit aws_ireland_fusionv2_nvme_cpu_current.yml --dryrun
seqerakit aws_ireland_fusionv2_nvme_cpu_arm_current.yml --dryrun
seqerakit aws_ireland_fusionv2_nvme_gpu_current.yml --dryrun

# Delete environments
seqerakit aws_ireland_fusionv2_nvme_cpu_current.yml --delete
seqerakit aws_ireland_fusionv2_nvme_cpu_arm_current.yml --delete
seqerakit aws_ireland_fusionv2_nvme_gpu_current.yml --delete
```

## GitOps Workflow

This repository implements GitOps integrated with the main Pulumi AWSMegatests project:

- **Pulumi Integration**: Compute environment deployment is managed through the parent Pulumi project
- **Automated Secrets**: Compute environment IDs and credentials automatically pushed to GitHub secrets
- **1Password Integration**: Secure credential management with `.envrc` and Pulumi 1Password provider
- **Infrastructure as Code**: All environments managed through version control

## Infrastructure Files

### Current Production Files

- `aws_ireland_fusionv2_nvme_cpu_current.yml` → `current-env-cpu.json`
- `aws_ireland_fusionv2_nvme_cpu_arm_current.yml` → `current-env-cpu-arm.json`
- `aws_ireland_fusionv2_nvme_gpu_current.yml` → `current-env-gpu.json`

### Configuration Structure

Each YAML file references an exported JSON configuration:

```yaml
compute-envs:
  - name: "environment_name"
    workspace: "$ORGANIZATION_NAME/$WORKSPACE_NAME"
    credentials: "$AWS_CREDENTIALS_NAME"
    wait: "AVAILABLE"
    file-path: "./current-env-[type].json"
    overwrite: True
```

### JSON Configuration Structure

Each JSON file contains the complete compute environment configuration:

```json
{
  "discriminator": "aws-batch",
  "region": "eu-west-1",
  "executionRole": "arn:aws:iam::...:role/TowerForge-...-ExecutionRole",
  "headJobRole": "arn:aws:iam::...:role/TowerForge-...-FargateRole",
  "workDir": "s3://nf-core-awsmegatests",
  "headJobCpus": 4,
  "headJobMemoryMb": 16384,
  "waveEnabled": true,
  "fusion2Enabled": true,
  "nvnmeStorageEnabled": true,
  "fusionSnapshots": true,
  "nextflowConfig": "aws.batch.maxSpotAttempts=5\nprocess {\n    maxRetries = 2\n    errorStrategy = { task.exitStatus in ((130..145) + 104 + 175) ? 'retry' : 'terminate' }\n}\n",
  "forge": {
    "type": "SPOT",
    "minCpus": 0,
    "maxCpus": 500,
    "gpuEnabled": false,
    "instanceTypes": ["c6id", "m6id", "r6id"],
    "allowBuckets": [
      "s3://ngi-igenomes",
      "s3://nf-core-awsmegatests",
      "s3://annotation-cache/"
    ],
    "fargateHeadEnabled": true
  }
}
```

## Environment Variables

The `.envrc` file defines key configuration variables:

```bash
export ORGANIZATION_NAME="nf-core"
export WORKSPACE_NAME="AWSmegatests"
export AWS_CREDENTIALS_NAME="tower-awstest"
export AWS_REGION="eu-west-1"
export AWS_WORK_DIR="s3://nf-core-awsmegatests"
export AWS_COMPUTE_ENV_ALLOWED_BUCKETS="s3://ngi-igenomes,s3://annotation-cache"
```

## Current Environment Status

All three compute environments are successfully deployed with fusion snapshots enabled:

✅ **CPU Environment**: Standard x86_64 instances with fusion snapshots
✅ **ARM Environment**: ARM Graviton instances with fusion snapshots  
✅ **GPU Environment**: GPU + CPU instances with fusion snapshots

## Environment IDs

For reference, the current environment IDs are:

- CPU: `53ljSqphNKjm6jjmuB6T9b` → `aws_ireland_fusionv2_nvme_cpu`
- ARM: `7eC1zALvNGIaFXbybVohP1` → `aws_ireland_fusionv2_nvme_cpu_ARM_snapshots`
- GPU: `2SRyFNKtLVAJCxMhcZRMfx` → `aws_ireland_fusionv2_nvme_gpu_snapshots`

## Technical Details

- **Cloud Provider**: AWS
- **Region**: eu-west-1 (Ireland)
- **Compute Backend**: AWS Batch
- **Container Technology**: Docker with Wave optimization
- **Storage**: S3 for work directory, NVMe for fast local storage
- **Networking**: Managed by Seqera Platform forge mode
- **Cost Optimization**: SPOT instances for all environments
- **Snapshots**: Enabled for optimized container layer caching using seqerakit's native `fusionSnapshots` field
