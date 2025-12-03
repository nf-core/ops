---
name: Managing Pulumi Stacks
description: Manage Pulumi stacks, view outputs, and configure stack settings. Use when switching stacks, viewing stack outputs, managing stack configuration, or working with multiple environments (dev, staging, production).
---

# Managing Pulumi Stacks

Manage Pulumi stacks for different environments and view stack state and outputs.

## When to Use

Use this skill when:

- Switching between stacks (dev, staging, production)
- Viewing stack outputs
- Managing stack configuration
- Listing available stacks
- Checking current stack state
- Working with multi-environment setups

## Common Stack Operations

### List Available Stacks

```bash
# List all stacks in current project
uv run pulumi stack ls

# Show current stack (marked with *)
uv run pulumi stack --show-name
```

### Switch Stacks

```bash
# Switch to a different stack
uv run pulumi stack select <stack-name>

# Examples:
uv run pulumi stack select development
uv run pulumi stack select production
uv run pulumi stack select AWSMegatests
```

### View Stack Outputs

```bash
# Show all stack outputs
uv run pulumi stack output

# Get specific output value
uv run pulumi stack output bucket_name

# Get output as JSON
uv run pulumi stack output --json

# Show secrets (requires passphrase)
uv run pulumi stack output --show-secrets
```

### View Stack Information

```bash
# Show detailed stack info
uv run pulumi stack

# Show stack with resource URNs
uv run pulumi stack --show-urns

# Show stack resources
uv run pulumi stack --show-ids
```

## Configuration Management

### View Configuration

```bash
# Show all config for current stack
uv run pulumi config

# Get specific config value
uv run pulumi config get aws:region

# Get secret config value
uv run pulumi config get database_password --show-secrets
```

### Set Configuration

```bash
# Set regular config value
uv run pulumi config set aws:region us-east-1

# Set secret config value (encrypted)
uv run pulumi config set database_password mypassword --secret

# Set config from file
uv run pulumi config set-all --plaintext < config.json
```

### Remove Configuration

```bash
# Remove config key
uv run pulumi config rm old_setting
```

## Stack Initialization

### Create New Stack

```bash
# Create and switch to new stack
uv run pulumi stack init <stack-name>

# Examples:
uv run pulumi stack init development
uv run pulumi stack init staging
```

### Remove Stack

**⚠️ Destructive operation - always confirm with user first!**

```bash
# Remove stack (must be empty)
uv run pulumi stack rm <stack-name>

# Force remove (dangerous!)
uv run pulumi stack rm <stack-name> --force
```

**Before removing:**

1. Confirm with user this is intentional
2. Export stack state for backup
3. Run `pulumi destroy` first to remove resources
4. Verify stack is empty with `pulumi stack`

## Quick Reference

| Task         | Command                                  |
| ------------ | ---------------------------------------- |
| List stacks  | `uv run pulumi stack ls`                 |
| Switch stack | `uv run pulumi stack select <name>`      |
| Create stack | `uv run pulumi stack init <name>`        |
| View outputs | `uv run pulumi stack output`             |
| View config  | `uv run pulumi config`                   |
| Set config   | `uv run pulumi config set <key> <value>` |
| Stack info   | `uv run pulumi stack`                    |

## Multi-Environment Workflow

### Standard Stack Naming

```
development    # For local development and testing
staging        # Pre-production testing
production     # Live production environment
```

### Environment-Specific Config

Each stack can have different configuration:

```bash
# Development stack
uv run pulumi stack select development
uv run pulumi config set instance_type t3.micro
uv run pulumi config set enable_monitoring false

# Production stack
uv run pulumi stack select production
uv run pulumi config set instance_type m5.large
uv run pulumi config set enable_monitoring true
```

### Accessing Config in Code

```python
import pulumi

config = pulumi.Config()
instance_type = config.get("instance_type") or "t3.small"
enable_monitoring = config.get_bool("enable_monitoring") or False
```

## Troubleshooting

Common issues and solutions:

### Stack Already Exists

```
error: stack 'production' already exists
```

**Solution**: Use `pulumi stack select production` to switch to it.

### Stack Not Found

```
error: no stack named 'staging' found
```

**Solution**: Create it with `pulumi stack init staging`.

### Config Key Not Found

```
error: configuration key 'aws:region' not found
```

**Solution**: Set it with `pulumi config set aws:region us-east-1`.

For more troubleshooting, see [troubleshooting.md](troubleshooting.md).

## Advanced Patterns

For complex stack management scenarios, see [reference.md](reference.md):

- Stack tagging and organization
- Cross-stack references
- Stack exports and imports
- Stack migrations
- Organization-level stack management

## Related Skills

- **Deploy**: Preview and deploy infrastructure changes
- **New Project**: Initialize new Pulumi projects with proper structure
- **Documentation**: Access Pulumi provider documentation
