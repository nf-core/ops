# Pulumi Troubleshooting Guide

Common issues and their solutions when working with Pulumi.

## Table of Contents

- [Authentication Issues](#authentication-issues)
- [State Backend Issues](#state-backend-issues)
- [Deployment Failures](#deployment-failures)
- [Configuration Problems](#configuration-problems)
- [Resource Issues](#resource-issues)
- [Performance Problems](#performance-problems)

## Authentication Issues

### AWS Credentials Not Found

**Error:**

```
error: get credentials: failed to refresh cached credentials, no EC2 IMDS role found
error: operation error S3: GetObject, get identity: get credentials
```

**Solutions:**

1. **Check environment variables:**

```bash
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY
echo $AWS_REGION
```

2. **If using direnv + 1Password:**

```bash
# Check .envrc exists and is allowed
direnv allow

# Verify credentials loaded
eval "$(direnv export bash)"
echo $AWS_ACCESS_KEY_ID
```

3. **Manually set credentials:**

```bash
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_REGION="us-east-1"
```

### Pulumi Passphrase Missing

**Error:**

```
error: failed to decrypt encrypted configuration value 'aws:secretKey': incorrect passphrase
```

**Solutions:**

1. **Set passphrase:**

```bash
export PULUMI_CONFIG_PASSPHRASE="your-passphrase"
```

2. **If using 1Password:**

```bash
# Add to .envrc
from_op PULUMI_CONFIG_PASSPHRASE="op://Employee/Pulumi Passphrase/password"
direnv allow
```

3. **Reset passphrase (if lost):**

```bash
# Export stack without secrets
uv run pulumi stack export > stack-backup.json

# Create new stack with new passphrase
uv run pulumi stack init new-stack

# Import (you'll lose encrypted secrets)
uv run pulumi stack import --file stack-backup.json
```

### 1Password Not Responding

**Error:**

```
direnv: error /path/to/.envrc is blocked. Run `direnv allow` to approve its content
```

**Solutions:**

1. **Allow direnv:**

```bash
direnv allow
```

2. **Check 1Password CLI:**

```bash
# Test 1Password access
op whoami

# If not signed in
eval $(op signin)
```

3. **Check service account token:**

```bash
echo $OP_SERVICE_ACCOUNT_TOKEN
```

## State Backend Issues

### Cannot Access S3 Backend

**Error:**

```
error: read ".pulumi/meta.yaml": operation error S3: GetObject
```

**Solutions:**

1. **Check AWS credentials** (see above)

2. **Verify S3 bucket exists:**

```bash
aws s3 ls s3://your-pulumi-state-bucket/
```

3. **Check bucket permissions:**

```bash
aws s3api get-bucket-policy --bucket your-pulumi-state-bucket
```

4. **Switch to local backend temporarily:**

```bash
export PULUMI_BACKEND_URL="file://~/.pulumi"
uv run pulumi login file://~/.pulumi
```

### Stack Already Exists

**Error:**

```
error: stack 'production' already exists
```

**Solution:**

Switch to existing stack instead of creating:

```bash
uv run pulumi stack select production
```

### Stack Not Found

**Error:**

```
error: no stack named 'staging' found
```

**Solutions:**

1. **List available stacks:**

```bash
uv run pulumi stack ls
```

2. **Create the stack if needed:**

```bash
uv run pulumi stack init staging
```

3. **Check you're in correct project:**

```bash
cat Pulumi.yaml  # Verify project name
```

## Deployment Failures

### Resource Already Exists

**Error:**

```
error: resource 'my-bucket' already exists
```

**Solutions:**

1. **Import existing resource:**

```bash
uv run pulumi import aws:s3/bucket:Bucket my-bucket existing-bucket-name
```

2. **Use different name:**

```python
# Add unique suffix
bucket = aws.s3.Bucket(f"my-bucket-{pulumi.get_stack()}")
```

3. **Delete existing resource** (if safe):

```bash
aws s3 rb s3://existing-bucket-name --force
```

### Insufficient Permissions

**Error:**

```
error: AccessDenied: User is not authorized to perform: s3:PutObject
```

**Solutions:**

1. **Check IAM permissions:**

```bash
aws iam get-user
aws iam list-attached-user-policies --user-name your-user
```

2. **Add required permissions** to IAM policy

3. **Use different credentials** with proper permissions

### Resource Update Failed

**Error:**

```
error: update failed: resource changes are not allowed
```

**Solutions:**

1. **Use replacement instead:**

```bash
uv run pulumi up --replace urn:pulumi:stack::project::Type::resource
```

2. **Check for protection:**

```python
# Remove protect flag if set
resource = Resource("name",
    opts=ResourceOptions(protect=False)
)
```

3. **Manual intervention required** - update resource manually, then refresh:

```bash
uv run pulumi refresh
```

## Configuration Problems

### Config Key Not Found

**Error:**

```
error: configuration key 'aws:region' not found
```

**Solution:**

Set the required config:

```bash
uv run pulumi config set aws:region us-east-1
```

### Secret Cannot Be Decrypted

**Error:**

```
error: failed to decrypt encrypted configuration value
```

**Solutions:**

1. **Set correct passphrase:**

```bash
export PULUMI_CONFIG_PASSPHRASE="correct-passphrase"
```

2. **Re-encrypt with new passphrase:**

```bash
# Export config without secrets
uv run pulumi config --show-secrets > config.txt

# Change passphrase
export PULUMI_CONFIG_PASSPHRASE="new-passphrase"

# Re-import configs as secrets
uv run pulumi config set key value --secret
```

### Wrong Stack Selected

**Problem:** Making changes to wrong environment

**Solution:**

Always verify current stack before deploying:

```bash
# Check current stack
uv run pulumi stack --show-name

# Should output: production

# If wrong, switch
uv run pulumi stack select production
```

**Best Practice:** Add stack name to shell prompt:

```bash
# Add to .bashrc or .zshrc
export PS1="[$(pulumi stack --show-name 2>/dev/null || echo 'no-stack')] $PS1"
```

## Resource Issues

### Dependency Cycle Detected

**Error:**

```
error: cycle: a -> b -> c -> a
```

**Solution:**

Break the cycle using explicit dependencies:

```python
# Instead of circular dependencies
a = Resource("a", dependency=b.output)
b = Resource("b", dependency=c.output)
c = Resource("c", dependency=a.output)

# Use explicit depends_on
a = Resource("a", opts=ResourceOptions(depends_on=[b]))
b = Resource("b", opts=ResourceOptions(depends_on=[c]))
c = Resource("c")  # No dependency on a
```

### Resource Still in Use

**Error:**

```
error: resource still has dependencies
```

**Solutions:**

1. **Delete dependent resources first**
2. **Use targeted destroy:**

```bash
uv run pulumi destroy --target dependent-resource
uv run pulumi destroy --target main-resource
```

3. **Force delete** (dangerous):

```bash
uv run pulumi state delete urn:pulumi:stack::project::Type::resource --force
```

### Timeout Waiting for Resource

**Error:**

```
error: timeout while waiting for resource to reach running state
```

**Solutions:**

1. **Increase timeout:**

```python
resource = Resource("name",
    opts=ResourceOptions(custom_timeouts=CustomTimeouts(
        create="30m",
        update="20m",
        delete="10m"
    ))
)
```

2. **Check resource manually:**

```bash
# For AWS resources
aws ec2 describe-instances --instance-ids i-xxxxx
```

3. **Cancel and retry:**

```bash
uv run pulumi cancel
uv run pulumi up
```

## Performance Problems

### Slow Deployments

**Symptoms:** Deployments taking excessively long

**Solutions:**

1. **Increase parallelism:**

```bash
uv run pulumi up --parallel 20
```

2. **Split large stacks** into smaller ones

3. **Use refresh less frequently:**

```bash
# Skip refresh on preview
uv run pulumi preview --skip-refresh
```

4. **Enable performance logging:**

```bash
export PULUMI_DEBUG_PROMISE_LEAKS=true
uv run pulumi up
```

### Large State File

**Symptoms:** Slow operations, large .pulumi/ directory

**Solutions:**

1. **Clean up deleted resources:**

```bash
uv run pulumi state delete urn:pulumi:stack::project::Type::old-resource --yes
```

2. **Split into multiple stacks**

3. **Export and re-import to compact:**

```bash
uv run pulumi stack export > stack.json
uv run pulumi stack rm --force
uv run pulumi stack init
uv run pulumi stack import --file stack.json
```

### Memory Issues

**Error:**

```
JavaScript heap out of memory
```

**Solutions:**

1. **Increase Node.js memory:**

```bash
export NODE_OPTIONS="--max-old-space-size=4096"
```

2. **Reduce parallelism:**

```bash
uv run pulumi up --parallel 5
```

## Getting More Help

### Enable Verbose Logging

```bash
# Maximum verbosity
uv run pulumi up --logtostderr -v=9

# Save to file
uv run pulumi up --logtostderr -v=9 2>&1 | tee pulumi-debug.log
```

### Check Pulumi Version

```bash
pulumi version
```

Update if needed:

```bash
brew upgrade pulumi  # macOS
# or
curl -fsSL https://get.pulumi.com | sh
```

### Community Resources

- **Pulumi Slack**: https://slack.pulumi.com
- **GitHub Issues**: https://github.com/pulumi/pulumi/issues
- **Documentation**: https://www.pulumi.com/docs/
- **Examples**: https://github.com/pulumi/examples

### Creating Bug Reports

When reporting issues:

1. **Pulumi version**: `pulumi version`
2. **Minimal reproduction case**
3. **Full error output** with `-v=9`
4. **Stack export** (without secrets)
5. **Provider versions**

```bash
# Gather debug info
pulumi version > debug-info.txt
uv run pulumi stack export >> debug-info.txt
uv run pulumi up --logtostderr -v=9 2>&1 | tee pulumi-error.log
```
