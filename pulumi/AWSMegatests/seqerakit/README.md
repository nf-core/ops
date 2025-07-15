# nf-core megatest seqerakit

Contains the seqerakit configurations for the three core compute environments used in nf-core megatests on the Seqera Platform.

## Quick Start

1. Install seqerakit: `pip install seqerakit`
2. Install Tower CLI v0.13.0+: Follow [installation guide](https://docs.seqera.io/platform/23.3.0/cli/overview)
3. Install direnv: `brew install direnv`
4. Allow environment loading: `direnv allow`
5. Deploy compute environments:
   ```bash
   seqerakit aws_ireland_fusionv2_nvme_cpu_current.yml
   seqerakit aws_ireland_fusionv2_nvme_cpu_arm_current.yml
   seqerakit aws_ireland_fusionv2_nvme_gpu_current.yml
   ```

## Architecture

### Three Core Compute Environments

This repository manages **three compute environments** on AWS Batch, all with fusion snapshots enabled:

#### 1. **CPU Environment** (`aws_ireland_fusionv2_nvme_cpu_snapshots`)

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

All three environments have fusion snapshots enabled using the Tower CLI v0.13.0+ format:

```json
{
  "fusionSnapshots": true,
  "fusion2Enabled": true,
  "waveEnabled": true,
  "nvnmeStorageEnabled": true
}
```

This replaces the previous configuration method that embedded snapshots settings in `nextflowConfig`.

## GitOps Workflow

This repository implements GitOps with GitHub Actions:

- **Pull Requests**: Automatically validate configurations with `--dryrun`
- **Main Branch**: Automatically deploy infrastructure changes
- **1Password Integration**: Secure credential management with `.envrc`

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

## Deployment Commands

### Individual Environment Deployment

```bash
# CPU environment
seqerakit aws_ireland_fusionv2_nvme_cpu_current.yml

# ARM environment
seqerakit aws_ireland_fusionv2_nvme_cpu_arm_current.yml

# GPU environment
seqerakit aws_ireland_fusionv2_nvme_gpu_current.yml
```

### Validation (Dry Run)

```bash
# Validate individual configurations
seqerakit aws_ireland_fusionv2_nvme_cpu_current.yml --dryrun
seqerakit aws_ireland_fusionv2_nvme_cpu_arm_current.yml --dryrun
seqerakit aws_ireland_fusionv2_nvme_gpu_current.yml --dryrun
```

### Cleanup

```bash
# Delete environments
seqerakit aws_ireland_fusionv2_nvme_cpu_current.yml --delete
seqerakit aws_ireland_fusionv2_nvme_cpu_arm_current.yml --delete
seqerakit aws_ireland_fusionv2_nvme_gpu_current.yml --delete
```

## Resolved Issues

✅ **Snapshots enabled for all environments**: All three compute environments now have fusion snapshots enabled using the Tower CLI v0.13.0+ format with `"fusionSnapshots": true`.

✅ **GPU functionality**: GPU environment properly configured with GPU-enabled instances and fallback CPU instances.

✅ **Consistent configuration**: All environments follow the same patterns with appropriate instance types for their use cases.

## Environment IDs

For reference, the current environment IDs are:

- CPU: `53ljSqphNKjm6jjmuB6T9b` → `aws_ireland_fusionv2_nvme_cpu`
- ARM: `5LWYX9a2GxrIFiax8tn9DV` → `aws_ireland_fusionv2_nvme_cpu_ARM_snapshots`
- GPU: `7Gjp4zOBlhH9xMIlfs9LM2` → `aws_ireland_fusionv2_nvme_gpu_snapshots`

## Technical Details

- **Cloud Provider**: AWS
- **Region**: eu-west-1 (Ireland)
- **Compute Backend**: AWS Batch
- **Container Technology**: Docker with Wave optimization
- **Storage**: S3 for work directory, NVMe for fast local storage
- **Networking**: Managed by Seqera Platform forge mode
- **Cost Optimization**: SPOT instances for all environments
- **Snapshots**: Enabled for optimized container layer caching
