# GitHub Integration for AWS Megatests

This document describes the GitHub integration setup for the AWS Megatests infrastructure, including token requirements, permissions, and troubleshooting.

## Overview

The GitHub integration manages organization-level Actions variables and secrets for the nf-core organization. This includes:

- **Variables** (non-sensitive): Compute environment IDs, workspace IDs, S3 bucket names
- **Secrets** (sensitive): API tokens, legacy compatibility secrets

## Current Status

- ✅ **Variables**: Successfully managed via Pulumi with `delete_before_replace` workaround
- 📋 **Secrets**: Manual management via gh CLI commands (exported in Pulumi outputs)
- 🔧 **Workaround**: Variables automated, secrets provided as manual commands

## Token Permission Requirements

### Current Issue

The GitHub token stored in 1Password ("GitHub nf-core PA Token Pulumi") lacks sufficient permissions:

```
403 You must be an org admin or have the actions variables fine-grained permission
```

### Required Permissions

#### Option 1: Organization Admin (Classic PAT)

- Token scope: `admin:org`
- Provides full organization administration access
- **Not recommended** due to excessive privileges

#### Option 2: Fine-Grained PAT (Recommended)

- Organization permission: **"Administration"** with **"Write"** access
- Provides minimum required permissions for Actions variables/secrets
- More secure than full org admin access

## Fixing the Permission Issue

### Step 1: Create New Fine-Grained PAT

1. Go to GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Click "Generate new token"
3. Configure token:
   - **Name**: `nf-core-pulumi-actions-admin`
   - **Expiration**: 90 days (or as per organization policy)
   - **Resource owner**: `nf-core`
   - **Repository access**: All repositories (or specific repositories if preferred)
   - **Organization permissions**:
     - **Administration**: Read and write
     - **Actions**: Read (if needed for other operations)

### Step 2: Update Token in 1Password

1. Access 1Password item: "GitHub nf-core PA Token Pulumi" in "Dev" vault
2. Replace the credential field with the new fine-grained PAT
3. Update notes to reflect the token type and permissions

### Step 3: Test Integration

Run the following command to test the integration:

```bash
pulumi preview --diff
```

### Step 4: Enable Secrets (After Permission Fix)

Once the token has proper permissions, update the main program:

```python
# In __main__.py, change enable_secrets to True
github_resources = create_github_resources(
    github_provider,
    compute_env_ids,
    op_secrets["tower_workspace_id"],
    enable_secrets=True  # Enable after token upgrade
)
```

## Manual Secret Management (Current Implementation)

https://github.com/pulumi/pulumi-github/issues/250

Due to the GitHub provider issue, we use manual secret management:

### Current Implementation

- **Variables**: Automated via Pulumi with `delete_before_replace` workaround
- **Secrets**: Manual commands exported in Pulumi outputs
- **Integration**: Variables automatically updated, secrets require manual execution

### How It Works

1. Pulumi creates GitHub variables with `delete_before_replace=True`
2. For secrets, manual gh CLI commands are generated and exported in stack outputs
3. The Tower access token and compute environment IDs are dynamically injected into command templates
4. Users run the exported commands to set secrets manually

### Running the Manual Commands

After deploying the infrastructure, get the commands from Pulumi outputs:

```bash
# Get the manual secret commands
pulumi stack output github_resources

# Set the TOWER_ACCESS_TOKEN environment variable
export TOWER_ACCESS_TOKEN="your-tower-access-token"

# Run the exported commands (examples):
gh secret set TOWER_ACCESS_TOKEN --org nf-core --body "$TOWER_ACCESS_TOKEN"
gh secret set TOWER_WORKSPACE_ID --org nf-core --body "59994744926013"
gh secret set TOWER_COMPUTE_ENV --org nf-core --body "<actual-cpu-compute-env-id>"
```

## Resources Managed

### Variables (Non-Sensitive)

- `TOWER_COMPUTE_ENV_CPU`: CPU compute environment ID
- `TOWER_COMPUTE_ENV_GPU`: GPU compute environment ID
- `TOWER_COMPUTE_ENV_ARM`: ARM compute environment ID
- `TOWER_WORKSPACE_ID`: Seqera Platform workspace ID
- `AWS_S3_BUCKET`: Legacy S3 bucket name

### Secrets (Sensitive)

- `TOWER_ACCESS_TOKEN`: Seqera Platform API token (manual management)
- `TOWER_WORKSPACE_ID`: Legacy secret version of workspace ID
- `TOWER_COMPUTE_ENV`: Legacy secret version of CPU compute environment ID

## Architecture Decisions

### Why Fine-Grained PATs?

1. **Principle of Least Privilege**: Only grants necessary permissions
2. **Security**: Reduced blast radius if token is compromised
3. **Compliance**: Aligns with GitHub security best practices
4. **Auditability**: Clear permission boundaries for compliance

### Why Separate Variables and Secrets?

1. **Permission Requirements**: Variables require different permissions than secrets
2. **Sensitivity**: Variables are non-sensitive configuration, secrets contain API tokens
3. **Troubleshooting**: Allows partial functionality when permission issues occur
4. **Migration**: Enables gradual migration from manual to automated management

## Troubleshooting

### Permission Errors

```
403 You must be an org admin or have the actions variables fine-grained permission
```

**Solution**: Upgrade token permissions as described above

### Token Not Found in 1Password

**Solution**: Verify 1Password provider configuration and item title/vault

### Variables Created But Not Secrets

**Expected**: Current configuration creates variables automatically but requires manual secret management

### Pulumi State Issues

If resources exist manually but not in Pulumi state:

```bash
# Import existing resources (replace with actual resource IDs)
pulumi import github:index/actionsOrganizationVariable:ActionsOrganizationVariable tower-compute-env-cpu TOWER_COMPUTE_ENV_CPU
```

## References

- [GitHub Fine-grained PATs Documentation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token)
- [GitHub Actions Variables Documentation](https://docs.github.com/en/actions/learn-github-actions/variables)
- [Pulumi GitHub Provider Documentation](https://www.pulumi.com/registry/packages/github/)
