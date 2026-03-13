---
name: Deploying Pulumi Infrastructure
description: Preview and deploy infrastructure changes using Pulumi. Use when deploying infrastructure, running pulumi up/preview, or applying infrastructure changes. Includes credential management with 1Password and safety confirmations for destructive operations.
---

# Deploying Pulumi Infrastructure

Deploy and manage infrastructure changes safely using Pulumi's preview and deployment workflow.

## When to Use

Use this skill when:

- Deploying infrastructure changes
- Previewing changes before applying
- Running `pulumi up` or `pulumi preview`
- Applying infrastructure as code
- Managing infrastructure updates

## Standard Deployment Workflow

Follow this safe deployment pattern:

### 1. Load Credentials

Ensure AWS and Pulumi credentials are available:

```bash
# If using direnv + 1Password (recommended):
# Credentials auto-load from .envrc when entering directory
cd path/to/pulumi/project

# Verify credentials loaded:
echo $AWS_ACCESS_KEY_ID  # Should show key
echo $PULUMI_CONFIG_PASSPHRASE  # Should show value
```

**If credentials not loaded**: Check `.envrc` exists and direnv is allowed (`direnv allow`).

### 2. Preview Changes

**Always preview before deploying:**

```bash
uv run pulumi preview
```

Review the output carefully:

- **Green `+`**: Resources to be created
- **Yellow `~`**: Resources to be modified
- **Red `-`**: Resources to be deleted

**⚠️ If resources will be deleted or modified in unexpected ways, STOP and investigate before proceeding.**

### 3. Confirm with User

Before running `pulumi up`, **always confirm with the user**:

- Summarize the changes from the preview
- Highlight any destructive operations (deletes, replacements)
- Ask: "Should I proceed with deployment?"
- Wait for explicit confirmation

### 4. Deploy Changes

Only after user confirmation:

```bash
uv run pulumi up --yes
```

The `--yes` flag auto-approves the deployment (safe since user already confirmed based on preview).

### 5. Verify Deployment

After successful deployment:

```bash
# View stack outputs
uv run pulumi stack output

# Check resource state
uv run pulumi stack --show-urns
```

## Quick Reference Commands

```bash
# Preview changes (dry-run)
uv run pulumi preview

# Deploy with automatic approval
uv run pulumi up --yes

# Deploy and save detailed output
uv run pulumi up --yes 2>&1 | tee deployment.log

# View current stack state
uv run pulumi stack

# Export stack configuration
uv run pulumi stack export > stack-backup.json
```

## Safety Checklist

Before deploying, verify:

- [ ] Credentials are loaded (AWS, Pulumi passphrase)
- [ ] Working in correct Pulumi project directory
- [ ] Correct stack selected (`pulumi stack select <stack>`)
- [ ] Preview shows expected changes
- [ ] No unexpected deletions or replacements
- [ ] User has confirmed deployment
- [ ] Backup of current state if making major changes

## Error Handling

If deployment fails:

1. **Read the error message carefully** - Pulumi provides detailed errors
2. **Check credentials** - Most failures are authentication issues
3. **Verify permissions** - IAM/RBAC issues are common
4. **Review stack state** - `pulumi stack` shows current state
5. **Consult troubleshooting guide** - See [../stack-management/troubleshooting.md](../stack-management/troubleshooting.md)

## Advanced Patterns

For more complex deployment scenarios, see [reference.md](reference.md):

- Targeted deployments (specific resources)
- Refresh operations
- Import existing infrastructure
- Parallel deployments
- CI/CD integration patterns

## Related Skills

- **Stack Management**: Switch stacks, view outputs, manage configuration
- **New Project**: Initialize new Pulumi projects with proper structure
- **Documentation**: Access Pulumi provider documentation
