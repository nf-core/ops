# AWS Megatests - OpenTofu Infrastructure

## Project Overview

OpenTofu IaC project managing nf-core's AWS megatest infrastructure. Integrates AWS, Seqera Platform, GitHub, and 1Password.

## Common Commands

```bash
tofu init                    # Initialize providers
tofu plan                    # Preview changes
tofu apply                   # Deploy
tofu fmt -check              # Check formatting
tofu output                  # View outputs
```

## Architecture

### File Layout

- `versions.tf` / `providers.tf` / `variables.tf` — scaffold
- `onepassword.tf` — 1Password data sources for secrets
- `locals.tf` — Nextflow config merging + shared forge defaults
- `s3.tf` — S3 bucket (imported), lifecycle rules, CORS
- `iam.tf` — TowerForge IAM user + 3 policies + access keys
- `seqera_credentials.tf` — AWS creds uploaded to Seqera Platform
- `github_credential.tf` — GitHub fine-grained token in Seqera
- `compute_environments.tf` — 3 compute envs (CPU, GPU, ARM)
- `github.tf` — 5 GitHub org variables
- `participants.tf` — workspace participant sync via scripts
- `outputs.tf` — all stack outputs

### Key Values

- **Region**: eu-west-1
- **S3 Bucket**: nf-core-awsmegatests
- **Workspace ID**: 59994744926013
- **Org ID**: 252464779077610
- **Seqera API**: https://api.cloud.seqera.io

### Secrets (from 1Password)

All secrets come from the `Dev` vault via `onepassword` provider:
- `Seqera Platform` — TOWER_ACCESS_TOKEN
- `AWS megatests` — IAM access keys (for reference, not used directly)
- `GitHub nf-core PA Token Pulumi` — GitHub token
- `GitHub nf-core Org Token` — Platform GitHub org token

### Kept As-Is

- `configs/` — Nextflow config files (read by TF via `file()`)
- `scripts/` — team management Python scripts (run via `null_resource`)
