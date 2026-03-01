"""iGenomes S3 Infrastructure Management

A Pulumi program for managing the ngi-igenomes S3 bucket infrastructure.

This project imports and tracks the AWS Open Data Registry iGenomes bucket,
providing infrastructure-as-code documentation and reference for nf-core projects.

Usage:
    # Preview changes
    direnv exec . uv run pulumi preview

    # Deploy/import resources
    direnv exec . uv run pulumi up

    # View outputs
    direnv exec . uv run pulumi stack output
"""

import pulumi

# Import our modular components
from src.config import get_configuration, validate_configuration
from src.providers import create_aws_provider
from src.infrastructure import import_igenomes_bucket, get_bucket_metadata


def main():
    """Main Pulumi program function."""

    # Step 1: Load and validate configuration
    pulumi.log.info("Loading configuration from environment...")
    config = get_configuration()
    validate_configuration(config)

    # Step 2: Create AWS provider
    pulumi.log.info(f"Creating AWS provider for region {config['aws_region']}...")
    aws_provider = create_aws_provider(config)

    # Step 3: Import iGenomes S3 bucket
    pulumi.log.info("Importing ngi-igenomes S3 bucket...")
    s3_resources = import_igenomes_bucket(aws_provider)
    igenomes_bucket = s3_resources["bucket"]

    # Step 4: Get bucket metadata
    bucket_metadata = get_bucket_metadata()

    # Exports - Provide useful outputs for reference
    pulumi.export(
        "bucket_info",
        {
            "name": igenomes_bucket.bucket,
            "arn": igenomes_bucket.arn,
            "region": bucket_metadata["region"],
            "description": bucket_metadata["description"],
            "access": bucket_metadata["access"],
        },
    )

    pulumi.export(
        "usage",
        {
            "s3_uri": bucket_metadata["usage"]["s3_uri"],
            "https_url": bucket_metadata["usage"]["https_url"],
            "cli_example": bucket_metadata["usage"]["cli_example"],
            "nextflow_config": bucket_metadata["usage"]["nextflow_config"],
        },
    )

    pulumi.export(
        "documentation",
        {
            "aws_open_data": "https://registry.opendata.aws/ngi-igenomes/",
            "github": bucket_metadata["github"],
            "docs": bucket_metadata["documentation"],
        },
    )

    pulumi.export(
        "resources",
        {
            "bucket": igenomes_bucket.id,
            "versioning": s3_resources["versioning"].id
            if s3_resources["versioning"]
            else "not-imported",
            "public_access_block": s3_resources["public_access_block"].id
            if s3_resources["public_access_block"]
            else "not-imported",
        },
    )

    pulumi.export(
        "notes",
        {
            "registry": "AWS Open Data Registry - publicly accessible",
            "permissions": "Read-only access via provided credentials",
            "management": "Bucket managed by AWS, tracked via Pulumi for reference",
            "cost": "No data transfer charges within same AWS region (eu-west-1)",
        },
    )


# Proper Pulumi program entry point
if __name__ == "__main__":
    main()
