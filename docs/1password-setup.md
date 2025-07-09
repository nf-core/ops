# 1Password Setup for nf-core/ops

This repository uses 1Password for secure credential management with direnv integration. This guide explains how to set up and use 1Password with the various projects in this repository.

## Prerequisites

1. **1Password CLI**: Install the 1Password CLI tool

   ```bash
   # macOS
   brew install --cask 1password-cli

   # Other platforms: https://developer.1password.com/docs/cli/get-started/
   ```

2. **direnv**: Install direnv for automatic environment loading

   ```bash
   # macOS
   brew install direnv

   # Add to your shell config (e.g., ~/.zshrc)
   eval "$(direnv hook zsh)"
   ```

3. **1Password Account Access**: Ensure you have access to the `nf-core` 1Password account

## Initial Setup

### 1. Sign in to 1Password CLI

```bash
# Sign in to the nf-core account
op signin --account nf-core

# Verify authentication
op whoami
```

### 2. Configure direnv

The repository uses the `direnv-1password` integration. When you enter a directory with a `.envrc` file, direnv will automatically:

- Load the 1Password integration script
- Fetch secrets from 1Password vaults
- Export them as environment variables

## Project-Specific Setup

### Seqerakit (AWS Megatests)

The `pulumi/AWSMegatests/seqerakit/` directory uses 1Password for storing:

- **Tower Access Token**: For Seqera Platform API access
- **AWS Credentials**: For AWS infrastructure management

#### Required 1Password Items

Ensure these items exist in the `Dev` vault:

1. **"Tower nf-core Access Token"**

   - Contains the Seqera Platform access token
   - Field: `password`

2. **"AWS Tower Test Credentials"**
   - Contains AWS access credentials for testing
   - Fields: `access key id`, `secret access key`

#### Usage

```bash
# Navigate to the seqerakit directory
cd pulumi/AWSMegatests/seqerakit/

# direnv will automatically prompt to allow the .envrc file
direnv allow

# Verify environment variables are loaded
echo $TOWER_ACCESS_TOKEN
echo $AWS_ACCESS_KEY_ID
```

## Environment File Structure

The `.envrc` files in this repository follow this pattern:

```bash
# Set the 1Password account
export OP_ACCOUNT=nf-core

# Load 1Password integration for direnv
source_url "https://github.com/tmatilai/direnv-1password/raw/v1.0.1/1password.sh" \
    "sha256-4dmKkmlPBNXimznxeehplDfiV+CvJiIzg7H1Pik4oqY="

# Load secrets from 1Password
from_op <<OP
    TOWER_ACCESS_TOKEN="op://Dev/Tower nf-core Access Token/password"
    AWS_ACCESS_KEY_ID="op://Dev/AWS Tower Test Credentials/access key id"
    AWS_SECRET_ACCESS_KEY="op://Dev/AWS Tower Test Credentials/secret access key"
OP

# Static configuration variables
export ORGANIZATION_NAME="nf-core"
export WORKSPACE_NAME="AWSmegatests"
# ... other static variables
```

## Security Best Practices

1. **Never commit secrets**: The `.envrc` files only contain 1Password references, never actual secrets
2. **Use vault organization**: Store secrets in appropriate 1Password vaults (`Dev`, `Prod`, etc.)
3. **Principle of least privilege**: Only grant access to necessary 1Password items
4. **Regular rotation**: Rotate access tokens and credentials regularly

## Troubleshooting

### Common Issues

1. **"op: not found"**

   - Install 1Password CLI: `brew install --cask 1password-cli`

2. **"Authentication required"**

   - Sign in: `op signin --account nf-core`

3. **"direnv: error .envrc is blocked"**

   - Allow the environment: `direnv allow`

4. **"Item not found"**

   - Verify the 1Password item exists in the specified vault
   - Check item name and field names match exactly

5. **"Permission denied"**
   - Ensure you have access to the `nf-core` 1Password account
   - Verify you have read access to the specified vault

### Debug Commands

```bash
# Test 1Password CLI access
op vault list

# Test specific item access
op item get "Tower nf-core Access Token" --vault Dev

# Check direnv status
direnv status

# Reload environment
direnv reload
```

## Adding New Projects

To add 1Password integration to a new project:

1. Create a `.envrc` file in the project directory
2. Add the 1Password integration script source
3. Define secret references using the `from_op` block
4. Store actual secrets in 1Password vaults
5. Document the required 1Password items

Example `.envrc` template:

```bash
export OP_ACCOUNT=nf-core

source_url "https://github.com/tmatilai/direnv-1password/raw/v1.0.1/1password.sh" \
    "sha256-4dmKkmlPBNXimznxeehplDfiV+CvJiIzg7H1Pik4oqY="

from_op <<OP
    YOUR_SECRET="op://VaultName/ItemName/field"
OP

export YOUR_CONFIG="static-value"
```

## References

- [1Password CLI Documentation](https://developer.1password.com/docs/cli/)
- [direnv Documentation](https://direnv.net/)
- [direnv-1password Integration](https://github.com/tmatilai/direnv-1password)
