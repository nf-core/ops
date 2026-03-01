"""Centralized constants and configuration values for iGenomes infrastructure."""

# S3 Configuration
S3_BUCKET_NAME = "ngi-igenomes"
S3_REGION = "eu-west-1"  # Ireland - same region as iGenomes bucket
S3_BUCKET_ARN = f"arn:aws:s3:::{S3_BUCKET_NAME}"

# iGenomes Metadata
IGENOMES_DESCRIPTION = "Illumina iGenomes reference genomes hosted on AWS Open Data Registry"
IGENOMES_SIZE_TB = 5  # Approximate size in terabytes
IGENOMES_ACCESS = "public-read"  # No authentication required

# AWS Configuration
AWS_ACCOUNT_OWNER = "Phil Ewels"  # From 1Password secret name
AWS_OPEN_DATA_REGISTRY = True  # Indicates this is an AWS Open Data bucket

# Project Metadata
PROJECT_NAME = "igenomes"
PROJECT_DESCRIPTION = "iGenomes S3 Infrastructure Management"
MANAGED_BY = "pulumi"
ORGANIZATION = "nf-core"

# Tags
DEFAULT_TAGS = {
    "project": PROJECT_NAME,
    "managed-by": MANAGED_BY,
    "organization": ORGANIZATION,
    "environment": "production",
    "purpose": "reference-genomes",
}
