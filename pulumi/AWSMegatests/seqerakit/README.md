# megatest-seqerakit

Contains the seqerakit scripts used to stand up the nf-core megatest workspace

## Quick Start

1. Install seqerakit: `pip install seqerakit`
2. Install direnv: `brew install direnv`
3. Allow environment loading: `direnv allow`
4. Deploy compute environments: `seqerakit aws_ireland_fusionv2_nvme_*_current.yml`

## GitOps Workflow

This repository now implements GitOps with GitHub Actions:

- **Pull Requests**: Automatically validate configurations with `--dryrun`
- **Main Branch**: Automatically deploy infrastructure changes
- **1Password Integration**: Secure credential management with `.envrc`

## Infrastructure Files

- **Current Production**: `*_current.yml` files reference exported JSON configurations
- **Legacy Templates**: `compute-envs/*.yml` files for reference
- **Exported Configs**: `current-env-*.json` files from Tower CLI export

## Resolved Issues

✅ **Snapshots with seqerakit**: Implemented in ARM environment (`current-env-cpu-arm.json`) with:

```json
"nextflowConfig": "fusion.enabled = true\nfusion.snapshots = true\nfusion.containerConfigUrl = '...'"
```

✅ **GPU-enabled compute environments**: Implemented in GPU environment (`current-env-gpu.json`) with:

```json
"forge": { "gpuEnabled": true, "instanceTypes": ["g4dn", "g5", "c6id", "m6id", "r6id"] }
```
