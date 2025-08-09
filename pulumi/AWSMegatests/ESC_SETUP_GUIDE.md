# Pulumi ESC Environment Setup Guide

This guide provides the essential documentation and resources for setting up Pulumi ESC environments properly.

## Essential Documentation Links

### Core ESC Documentation

1. **Main ESC Environment Guide:**  
   https://www.pulumi.com/docs/esc/environments/

2. **ESC Environment Configuration Reference:**  
   https://www.pulumi.com/docs/esc/reference/sample-environment-definition/

3. **Working with Environments:**  
   https://www.pulumi.com/docs/esc/environments/working-with-environments/

4. **ESC CLI Commands:**  
   https://www.pulumi.com/docs/esc/cli/commands/

5. **Pulumi-ESC Integration:**  
   https://www.pulumi.com/docs/esc/integrations/infrastructure/pulumi-iac/

### Specific Integration Guides

6. **AWS OIDC Configuration:**  
   https://www.pulumi.com/docs/esc/environments/configuring-oidc/aws/

7. **1Password Integration:**  
   https://www.pulumi.com/docs/esc/integrations/dynamic-login-credentials/1password-login/

## Key Concepts from Documentation

### Basic Environment Structure

```yaml
values:
  # Your configuration values go here
  aws:
    login:
      fn::open::aws-login:
        oidc:
          duration: 1h
          roleArn: arn:aws:iam::123456789012:role/your-role
          sessionName: pulumi-environments-session

  1password:
    secrets:
      fn::open::1password-secrets:
        login:
          serviceAccountToken:
            fn::secret:
              ciphertext: "encrypted-token-here"
        get:
          github-token:
            ref: "op://Dev/GitHub Token/password"

  environmentVariables:
    # Environment variables exposed when opening environment
    AWS_ACCESS_KEY_ID: ${aws.login.accessKeyId}
    AWS_SECRET_ACCESS_KEY: ${aws.login.secretAccessKey}
    AWS_SESSION_TOKEN: ${aws.login.sessionToken}
    GITHUB_TOKEN: ${1password.secrets.github-token}

  pulumiConfig:
    # Configuration exposed to Pulumi stacks
    aws:region: us-west-1
```

### CLI Commands for Setting Values

#### Basic Value Setting

```bash
# Set a simple value
esc env set org/project/environment path.to.value "my-value"

# Set a secret
esc env set org/project/environment path.to.secret --secret "secret-value"

# Set a plaintext value (when ESC thinks it's a secret)
esc env set org/project/environment path.to.value --plaintext "my-value"
```

#### Complex Object Creation

```bash
# Create empty objects first
esc env set org/project/environment values '{}'
esc env set org/project/environment values.aws '{}'
esc env set org/project/environment values.aws.login '{}'

# Then populate the nested values
esc env set org/project/environment 'values.aws.login.fn::open::aws-login' '{}'
esc env set org/project/environment 'values.aws.login.fn::open::aws-login.oidc' '{}'
esc env set org/project/environment 'values.aws.login.fn::open::aws-login.oidc.duration' "1h"
```

### Environment Import in Pulumi Stack

#### Stack Configuration File (Pulumi.prod.yaml)

```yaml
environment:
  - project/environment-name
```

#### Environment Reference Format

- ✅ Correct: `project/environment` (single slash)
- ❌ Incorrect: `org/project/environment` (multiple slashes not supported in stack config)

### Best Practices from Documentation

#### 1. Use `esc env edit` for Complex Configurations

For complex configurations, the documentation recommends using:

```bash
esc env edit org/project/environment
```

This opens your default editor and is easier than multiple `esc env set` commands.

#### 2. Environment Composition

```yaml
imports:
  - shared/common
  - aws/production
values:
  # Environment-specific overrides
```

#### 3. Secret Handling

- Use `fn::secret:` for inline secrets
- Use `fn::open::1password-secrets` for external secret providers
- Mark CLI values with `--secret` flag when needed

#### 4. Environment Variables vs Pulumi Config

- `environmentVariables`: Available when running `esc open` or `esc run`
- `pulumiConfig`: Available to Pulumi stacks that import the environment

## Common Patterns

### AWS OIDC + 1Password Pattern

```yaml
values:
  aws:
    login:
      fn::open::aws-login:
        oidc:
          duration: 1h
          roleArn: ${aws.oidc.roleArn}
          sessionName: pulumi-environments-session

  1password:
    secrets:
      fn::open::1password-secrets:
        login:
          serviceAccountToken:
            fn::secret:
              ciphertext: "your-encrypted-token"
        get:
          github-token:
            ref: "op://Vault/Item/field"

  environmentVariables:
    AWS_ACCESS_KEY_ID: ${aws.login.accessKeyId}
    AWS_SECRET_ACCESS_KEY: ${aws.login.secretAccessKey}
    AWS_SESSION_TOKEN: ${aws.login.sessionToken}
    GITHUB_TOKEN: ${1password.secrets.github-token}
```

### Multi-Environment Composition

```yaml
# Base environment
imports:
  - shared/aws-base
  - shared/secrets-base
values:
  environment: production
  # Production-specific overrides
```

## Troubleshooting Tips

### Common Issues

1. **"Missing required properties"**: Build nested objects incrementally
2. **"Secret values must be string literals"**: Use `--secret` flag or proper `fn::secret:` syntax
3. **"Unknown property"**: Ensure parent objects exist before setting child properties
4. **"Invalid environment reference"**: Check for multiple slashes in stack configuration

### Debugging Commands

```bash
# View current environment structure
esc env get org/project/environment

# Test environment opening
esc open org/project/environment

# List all environments
esc env ls
```

## Our Specific Use Case

For the `nf-core/AWSMegatestsProd/aws` environment, we need:

1. **AWS OIDC Configuration** for temporary credentials
2. **1Password Integration** for GitHub and Tower tokens
3. **Environment Variables** for all the AWS and application settings
4. **Updated Trust Policy** in AWS IAM to accept the new environment subject

The goal is to enable `uv run pulumi preview --stack prod` to work directly by referencing `AWSMegatestsProd/aws` in the `Pulumi.prod.yaml` file.
