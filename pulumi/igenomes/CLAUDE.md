# iGenomes - Claude Code Context

This file provides Claude Code with comprehensive context for the iGenomes Pulumi infrastructure project.

## Project Overview

This is a **Pulumi Infrastructure as Code (IaC) project** that manages and tracks the AWS iGenomes S3 bucket infrastructure. The project imports the existing `ngi-igenomes` bucket from AWS Open Data Registry for reference, documentation, and infrastructure tracking purposes.

**Key Distinction**: This project **does not actively manage** the bucket configuration (which is controlled by AWS Open Data Registry), but rather **imports and tracks** it in Pulumi state for:

- Documentation and reference
- Infrastructure-as-code best practices
- Integration with nf-core infrastructure ecosystem
- Metadata and usage information exports

## Architecture

### Code Organization

The codebase follows a modular structure inspired by the AWSMegatests project:

```
igenomes/
├── __main__.py              # Main Pulumi program entry point
├── src/                     # Organized source code
│   ├── config/              # Configuration management
│   │   └── settings.py      # Environment variable loading and validation
│   ├── providers/           # Provider configurations
│   │   └── aws.py           # AWS provider setup
│   ├── infrastructure/      # Infrastructure components
│   │   └── s3.py            # S3 bucket import logic
│   └── utils/               # Utilities and constants
│       └── constants.py     # Centralized configuration values
├── Pulumi.yaml              # Pulumi project configuration
├── pyproject.toml           # Python project configuration
└── .envrc                   # 1Password credential loading
```

**Module Responsibilities:**

- `config/`: Load and validate configuration from environment variables
- `providers/`: Configure cloud provider connections
- `infrastructure/`: Define and import infrastructure resources
- `utils/`: Shared constants and utility functions

### Core Components

#### 1. S3 Bucket Import

The project imports the existing `ngi-igenomes` bucket with protective measures:

```python
s3.Bucket(
    "ngi-igenomes",
    bucket=S3_BUCKET_NAME,
    opts=pulumi.ResourceOptions(
        import_=S3_BUCKET_NAME,  # Import from existing bucket
        protect=True,            # Prevent accidental deletion
        ignore_changes=[...],    # Don't manage properties we can't control
    )
)
```

**Protection Strategy:**

- `protect=True`: Prevents Pulumi from deleting the resource
- `ignore_changes`: Extensive list of properties we don't manage
- Read-only approach: Track but don't modify

#### 2. Credential Management

AWS credentials are loaded from 1Password via direnv:

```bash
# .envrc
export AWS_ACCESS_KEY_ID=$(op item get "AWS - Phil - iGenomes" --vault "Shared" --fields "Access Key")
export AWS_SECRET_ACCESS_KEY=$(op item get "AWS - Phil - iGenomes" --vault "Shared" --fields "Secret Key")
```

**Security Features:**

- Credentials never committed to git
- Loaded at runtime via 1Password CLI
- Automatic validation in `get_configuration()`

#### 3. Metadata Exports

The project exports comprehensive metadata for reference:

- **bucket_info**: Bucket name, ARN, region, description
- **usage**: S3 URIs, HTTPS URLs, CLI examples, Nextflow config
- **documentation**: Links to AWS Open Data, GitHub, docs
- **resources**: Pulumi resource IDs for tracking
- **notes**: Important operational information

### File Structure Details

#### `__main__.py`

Main Pulumi program that:

1. Loads configuration from environment
2. Creates AWS provider
3. Imports S3 bucket and related resources
4. Exports metadata and usage information

#### `src/config/settings.py`

Configuration management:

- Loads AWS credentials from environment variables
- Validates required configuration keys
- Raises clear errors if credentials missing

#### `src/providers/aws.py`

AWS provider configuration:

- Creates provider with credentials from config
- Sets region to `eu-west-1` (Ireland)
- Matches iGenomes bucket location

#### `src/infrastructure/s3.py`

S3 infrastructure import:

- Imports existing `ngi-igenomes` bucket
- Attempts to import related configurations (versioning, public access)
- Handles permission errors gracefully
- Provides metadata function for exports

#### `src/utils/constants.py`

Centralized constants:

- Bucket name and ARN
- Region configuration
- iGenomes metadata
- Default tags

## Common Commands

### Prerequisites

```bash
# Install dependencies
uv sync

# Authenticate with 1Password
eval $(op signin)

# Allow environment variables
direnv allow

# Login to Pulumi
pulumi login s3://nf-core-pulumi-state?region=eu-north-1&awssdk=v2
```

### Development Workflow

```bash
# Preview infrastructure changes
direnv exec . uv run pulumi preview

# Import S3 bucket (first time)
direnv exec . uv run pulumi up

# View outputs
direnv exec . uv run pulumi stack output

# Refresh state to match actual infrastructure
direnv exec . uv run pulumi refresh
```

### State Management

```bash
# List stack resources
direnv exec . uv run pulumi stack --show-urns

# View specific resource
direnv exec . uv run pulumi stack --show-urns | grep ngi-igenomes

# Refresh state
direnv exec . uv run pulumi refresh
```

## Key Technologies

### Pulumi Providers Used

1. **AWS Provider** (`pulumi-aws`)
   - Imports S3 bucket resources
   - Uses credentials from 1Password
   - Region: `eu-west-1` (Ireland)

### Environment Configuration

The project uses **direnv + 1Password** for credential management:

```yaml
# Environment Variables (loaded via .envrc)
AWS_ACCESS_KEY_ID: From 1Password "AWS - Phil - iGenomes"
AWS_SECRET_ACCESS_KEY: From 1Password "AWS - Phil - iGenomes"
AWS_DEFAULT_REGION: "eu-west-1"
PULUMI_BACKEND_URL: "s3://nf-core-pulumi-state?region=eu-north-1&awssdk=v2"
```

## Development Guidelines

### When Working with This Project

1. **Use standard Pulumi commands** - direnv handles credential loading
2. **Never commit secrets** - all credentials managed through 1Password
3. **Test with preview** before importing: `direnv exec . uv run pulumi preview`
4. **Check outputs** after deployment: `direnv exec . uv run pulumi stack output`
5. **Understand limitations** - we track but don't manage bucket configuration

### Common Issues and Solutions

#### Credential Issues

**"Failed to load AWS credentials from 1Password"**

- **Solution**: Authenticate with 1Password: `eval $(op signin)`
- **Check**: Run `direnv allow` to reload environment variables
- **Verify**: Check 1Password secret exists: `op item get "AWS - Phil - iGenomes" --vault "Shared"`

**"Invalid AWS credentials"**

- **Solution**: Verify credentials are correct in 1Password
- **Check**: Test with AWS CLI: `aws s3 --region eu-west-1 ls s3://ngi-igenomes/`
- **Note**: Credentials may be read-only for public bucket

#### Import Issues

**"Resource already exists in state"**

- **Cause**: Bucket already imported in previous run
- **Solution**: Use `pulumi refresh` to sync state
- **Alternative**: Delete from state first: `pulumi state delete <urn>`

**"Permission denied" on bucket configuration**

- **Expected**: AWS Open Data Registry manages bucket configuration
- **Solution**: This is normal - we use `ignore_changes` for these properties
- **Note**: We track bucket reference, not active configuration

#### State Management

**"State out of sync with actual infrastructure"**

- **Solution**: Run `pulumi refresh` to sync state
- **Cause**: External changes to AWS resources
- **Prevention**: Use `protect=True` on critical resources

### Code Patterns

**Configuration Loading:**

```python
from src.config import get_configuration, validate_configuration

config = get_configuration()
validate_configuration(config)
```

**AWS Provider Creation:**

```python
from src.providers import create_aws_provider

aws_provider = create_aws_provider(config)
```

**S3 Bucket Import:**

```python
from src.infrastructure import import_igenomes_bucket, get_bucket_metadata

s3_resources = import_igenomes_bucket(aws_provider)
metadata = get_bucket_metadata()
```

## iGenomes Bucket Details

### Bucket Information

- **Name**: `ngi-igenomes`
- **Region**: `eu-west-1` (Ireland)
- **Size**: ~5TB of reference genome data
- **Access**: Public read (no authentication required)
- **Owner**: AWS Open Data Registry (managed by AWS)

### Data Organization

- **30+ species** reference genomes
- **Multiple sources**: Ensembl, NCBI, UCSC
- **Pre-built indices**: Bismark, Bowtie, Bowtie2, BWA, STAR
- **Annotation files**: GTF, BED formats
- **GATK bundles**: Human genome resources

### Usage Patterns

**Nextflow Pipelines:**

```groovy
params {
    igenomes_base = 's3://ngi-igenomes/igenomes'
    genome = 'GRCh38'
}
```

**AWS CLI (No Authentication):**

```bash
aws s3 --no-sign-request --region eu-west-1 ls s3://ngi-igenomes/
```

**Python (boto3):**

```python
import boto3
from botocore import UNSIGNED
from botocore.client import Config

s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
response = s3.list_objects_v2(Bucket='ngi-igenomes')
```

## Integration with nf-core Infrastructure

This project is part of the broader nf-core infrastructure ecosystem:

- **State Backend**: Shared S3 backend (`nf-core-pulumi-state`)
- **Credential Management**: Consistent 1Password patterns
- **Project Structure**: Follows AWSMegatests conventions
- **Documentation**: Comprehensive README and context files

### Related Projects

- **AWSMegatests**: AWS Batch compute environments for testing
- **pulumi_state**: S3 backend for Pulumi state storage
- **seqera_platform**: Seqera Platform workspace management

## Outputs and Monitoring

The stack provides several outputs for reference and integration:

```bash
# View all outputs
pulumi stack output

# Outputs provided:
bucket_info:         Bucket metadata (name, ARN, region, description)
usage:              Usage examples (S3 URIs, HTTPS URLs, CLI commands)
documentation:      External documentation links
resources:          Pulumi resource IDs
notes:              Important operational information
```

## Security Considerations

- **1Password Integration**: All credentials from 1Password vault
- **Read-Only Access**: Credentials provide read-only access to bucket metadata
- **Protected Resources**: All resources marked `protect=True`
- **No Secrets in Git**: `.gitignore` excludes all credential files
- **Public Bucket**: No authentication required for data access

## Cost Optimization

- **Zero cost** for bucket tracking (read-only import)
- **No data transfer charges** when accessing from `eu-west-1`
- **Optimal co-location** for compute in Ireland region
- **Public access** means no AWS charges for most operations

## Future Enhancements

Potential improvements:

1. Add bucket metrics and monitoring
2. Create CloudWatch dashboard for access patterns
3. Implement automated bucket inventory
4. Add data lifecycle documentation
5. Create integration examples for nf-core pipelines

## Related Documentation

- **Main README**: `README.md` - User-facing project documentation
- **Context7 Setup**: `CONTEXT7.md` - AWS SDK documentation integration
- **AWS iGenomes Docs**: https://ewels.github.io/AWS-iGenomes/
- **Pulumi AWS Provider**: https://www.pulumi.com/registry/packages/aws/

## Technical Details

- **Language**: Python 3.11+
- **Package Manager**: UV (fast Python package installer)
- **Cloud Provider**: AWS (eu-west-1)
- **State Backend**: S3 (nf-core-pulumi-state)
- **Credential Provider**: 1Password CLI
- **Project Type**: Infrastructure import and tracking
