# iGenomes - Pulumi Infrastructure Management

Infrastructure-as-Code management for the [AWS iGenomes](https://ewels.github.io/AWS-iGenomes/) S3 bucket using Pulumi.

## Overview

This Pulumi project imports and tracks the `ngi-igenomes` S3 bucket, which hosts ~5TB of reference genome data on the [AWS Open Data Registry](https://registry.opendata.aws/ngi-igenomes/). The bucket contains pre-built genomic references and indices used by nf-core pipelines and other bioinformatics workflows.

**Key Features:**

- 📦 S3 bucket import and state tracking
- 🔐 Secure credential management via 1Password
- 📊 Comprehensive infrastructure documentation
- 🏷️ Metadata and usage information exports
- 🛡️ Protected resources to prevent accidental deletion

## Quick Start

### Prerequisites

```bash
# Install UV (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install direnv (for environment variable management)
brew install direnv  # macOS
# or
sudo apt install direnv  # Ubuntu/Debian

# Install 1Password CLI
brew install --cask 1password-cli  # macOS
```

### Setup

```bash
# Navigate to project directory
cd pulumi/igenomes

# Authenticate with 1Password
eval $(op signin)

# Allow direnv to load environment variables
direnv allow

# Install Python dependencies
uv sync

# Login to Pulumi backend
pulumi login s3://nf-core-pulumi-state?region=eu-north-1&awssdk=v2

# Select or create stack
pulumi stack select dev --create
```

### Deploy

```bash
# Preview infrastructure changes
direnv exec . uv run pulumi preview

# Import S3 bucket (first time only)
direnv exec . uv run pulumi up

# View stack outputs
direnv exec . uv run pulumi stack output

# Refresh state to match actual infrastructure
direnv exec . uv run pulumi refresh
```

## Project Structure

```
igenomes/
├── __main__.py              # Main Pulumi program
├── Pulumi.yaml              # Project configuration
├── pyproject.toml           # Python dependencies
├── uv.lock                  # Locked dependencies
├── .envrc                   # 1Password credential loading
├── .gitignore               # Git ignore patterns
├── README.md                # This file
├── CLAUDE.md                # AI assistant context
├── CONTEXT7.md              # Context7 AWS SDK documentation
└── src/                     # Modular source code
    ├── config/              # Configuration management
    │   ├── __init__.py
    │   └── settings.py      # Environment variable loading
    ├── providers/           # Cloud provider setup
    │   ├── __init__.py
    │   └── aws.py           # AWS provider configuration
    ├── infrastructure/      # Infrastructure components
    │   ├── __init__.py
    │   └── s3.py            # S3 bucket import logic
    └── utils/               # Utility functions
        ├── __init__.py
        └── constants.py     # Project constants
```

## Architecture

### Infrastructure Components

#### S3 Bucket

- **Name**: `ngi-igenomes`
- **Region**: `eu-west-1` (Ireland)
- **Size**: ~5TB of reference genome data
- **Access**: Public read (no authentication required)
- **Registry**: AWS Open Data Registry

#### Resource Protection

All imported resources are protected from accidental deletion:

- `protect=True` on all resources
- `ignore_changes` for properties we cannot manage
- Read-only tracking via Pulumi state

#### Configuration Management

- AWS credentials from 1Password (`AWS - Phil - iGenomes`)
- Environment variables loaded via direnv
- Pulumi state stored in S3 backend

### Data Organization

The iGenomes bucket contains:

- **30+ species** reference genomes
- **Multiple sources** (Ensembl, NCBI, UCSC)
- **Pre-built indices** (Bismark, Bowtie, Bowtie2, BWA, STAR)
- **Annotation files** (GTF, BED formats)
- **GATK bundles** (human genomes)

## Usage

### Stack Outputs

```bash
# View all outputs
pulumi stack output

# View specific output
pulumi stack output bucket_info
pulumi stack output usage
pulumi stack output documentation
```

### Example Outputs

```json
{
  "bucket_info": {
    "name": "ngi-igenomes",
    "arn": "arn:aws:s3:::ngi-igenomes",
    "region": "eu-west-1",
    "description": "Illumina iGenomes reference genomes hosted on AWS Open Data Registry",
    "access": "public-read (no authentication required)"
  },
  "usage": {
    "s3_uri": "s3://ngi-igenomes",
    "https_url": "https://ngi-igenomes.s3.eu-west-1.amazonaws.com",
    "cli_example": "aws s3 --no-sign-request --region eu-west-1 ls s3://ngi-igenomes/",
    "nextflow_config": "params.igenomes_base = \"s3://ngi-igenomes/igenomes\""
  },
  "documentation": {
    "aws_open_data": "https://registry.opendata.aws/ngi-igenomes/",
    "github": "https://github.com/ewels/AWS-iGenomes",
    "docs": "https://ewels.github.io/AWS-iGenomes/"
  }
}
```

### Accessing iGenomes Data

#### AWS CLI (No Authentication)

```bash
# List bucket contents
aws s3 --no-sign-request --region eu-west-1 ls s3://ngi-igenomes/

# Download specific genome
aws s3 --no-sign-request --region eu-west-1 \
  cp s3://ngi-igenomes/igenomes/Homo_sapiens/UCSC/hg38/ ./hg38/ --recursive
```

#### Nextflow Configuration

```groovy
params {
    igenomes_base = 's3://ngi-igenomes/igenomes'
    genome = 'GRCh38'
}
```

#### Python (boto3)

```python
import boto3
from botocore import UNSIGNED
from botocore.client import Config

# Create S3 client with no signature (public bucket)
s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))

# List objects
response = s3.list_objects_v2(Bucket='ngi-igenomes', Prefix='igenomes/')
```

## Common Commands

### Pulumi Operations

```bash
# Preview changes
direnv exec . uv run pulumi preview

# Import resources
direnv exec . uv run pulumi up

# View outputs
direnv exec . uv run pulumi stack output

# Refresh state
direnv exec . uv run pulumi refresh

# View stack resources
direnv exec . uv run pulumi stack --show-urns

# Destroy stack (CAREFUL!)
direnv exec . uv run pulumi destroy
```

### Development

```bash
# Update dependencies
uv sync

# Run Python linting
uv run black src/
uv run ruff check src/

# Type checking
uv run mypy src/

# View Python environment
uv pip list
```

### Credential Management

```bash
# Check 1Password authentication
op whoami

# Re-authenticate if needed
eval $(op signin)

# Verify environment variables are loaded
echo $AWS_ACCESS_KEY_ID
echo $AWS_DEFAULT_REGION
```

## Troubleshooting

### "Failed to load AWS credentials from 1Password"

**Solution**: Ensure you're authenticated with 1Password:

```bash
eval $(op signin)
direnv allow
```

### "No such bucket: ngi-igenomes"

**Solution**: The bucket exists but may not be accessible. Verify AWS credentials:

```bash
aws s3 --no-sign-request --region eu-west-1 ls s3://ngi-igenomes/
```

### "Resource already exists in state"

**Solution**: The resource is already imported. Use `pulumi refresh` to sync state:

```bash
direnv exec . uv run pulumi refresh
```

### "Permission denied" on bucket operations

**Expected**: The credentials provide read-only access. The bucket is managed by AWS Open Data Registry, not this Pulumi project. We track it for reference and documentation purposes.

## Cost Optimization

- **Zero cost for data access** within `eu-west-1` region
- **No authentication required** for public access
- **No data transfer charges** for same-region access
- **Optimal for co-located compute** in Ireland (eu-west-1)

## Security Considerations

- AWS credentials stored securely in 1Password
- Credentials never committed to git
- Read-only access pattern
- Protected resources prevent accidental deletion
- Public bucket requires no authentication

## Development Guidelines

1. **Never commit secrets** - all credentials via 1Password
2. **Test with preview** before deploying changes
3. **Document changes** in commit messages
4. **Follow Python style** - use Black and Ruff
5. **Update documentation** when adding features

## References

- **AWS Open Data Registry**: https://registry.opendata.aws/ngi-igenomes/
- **iGenomes Documentation**: https://ewels.github.io/AWS-iGenomes/
- **GitHub Repository**: https://github.com/ewels/AWS-iGenomes
- **Pulumi AWS Provider**: https://www.pulumi.com/registry/packages/aws/
- **nf-core Pipelines**: https://nf-co.re/

## License

This infrastructure-as-code project is maintained by nf-core. The iGenomes data is provided by Illumina and hosted on AWS Open Data Registry.

## Support

For issues or questions:

- **nf-core Slack**: https://nf-co.re/join/slack
- **GitHub Issues**: Create an issue in the nf-core/ops repository
- **Documentation**: See CLAUDE.md for AI assistant context
