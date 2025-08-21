#!/usr/bin/env python3
"""
S3 Results Tagging Script

This script identifies and tags S3 results directories to manage orphaned
directories that cause "no AWS results found" issues on the website.

The script:
- Fetches current pipeline releases from pipelines.json
- Scans S3 bucket for all results-* directories
- Tags current releases with metadata (pipeline, release, sha, status)
- Tags orphaned directories with deleteme=true for future cleanup
"""

import boto3
import requests
import sys
import argparse
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def fetch_pipeline_data(pipelines_json_url: str) -> dict:
    """Fetch current pipeline release data"""
    try:
        logger.info(f"Fetching pipeline data from {pipelines_json_url}")
        response = requests.get(pipelines_json_url, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Build lookup of current release SHAs
        current_shas = {}
        for pipeline in data.get("remote_workflows", []):
            pipeline_name = pipeline["name"]
            for release in pipeline.get("releases", []):
                if release["tag_name"] != "dev":
                    sha = release.get("tag_sha")
                    if sha:
                        current_shas[f"{pipeline_name}/results-{sha}"] = {
                            "pipeline": pipeline_name,
                            "version": release["tag_name"],
                            "sha": sha,
                        }

        logger.info(f"Found {len(current_shas)} current release results directories")
        return current_shas
    except Exception as e:
        logger.error(f"Failed to fetch pipeline data: {e}")
        sys.exit(1)


def list_s3_results_directories(s3_bucket: str) -> list:
    """List all results-* directories in S3"""
    try:
        s3_client = boto3.client("s3")
        logger.info(f"Scanning S3 bucket {s3_bucket} for results directories")

        paginator = s3_client.get_paginator("list_objects_v2")
        results_dirs = set()

        # Look for all results- prefixes across all pipelines
        page_iterator = paginator.paginate(Bucket=s3_bucket, Delimiter="/")

        for page in page_iterator:
            # Get pipeline-level prefixes
            for prefix_info in page.get("CommonPrefixes", []):
                pipeline_prefix = prefix_info["Prefix"]

                # Look for results- directories within each pipeline
                pipeline_paginator = s3_client.get_paginator("list_objects_v2")
                pipeline_iterator = pipeline_paginator.paginate(
                    Bucket=s3_bucket, Prefix=pipeline_prefix, Delimiter="/"
                )

                for pipeline_page in pipeline_iterator:
                    for sub_prefix in pipeline_page.get("CommonPrefixes", []):
                        sub_dir = sub_prefix["Prefix"]
                        if "/results-" in sub_dir:
                            # Extract the results directory path
                            results_dir = sub_dir.rstrip("/")
                            results_dirs.add(results_dir)

        logger.info(f"Found {len(results_dirs)} results directories in S3")
        return list(results_dirs)
    except Exception as e:
        logger.error(f"Failed to list S3 directories: {e}")
        sys.exit(1)


def get_object_tags(s3_client, s3_bucket: str, prefix: str) -> dict:
    """Get existing tags for an S3 prefix by checking a representative object"""
    try:
        # Find a representative object in this prefix
        response = s3_client.list_objects_v2(
            Bucket=s3_bucket, Prefix=prefix + "/", MaxKeys=1
        )

        if "Contents" not in response or not response["Contents"]:
            return {}

        # Get tags from the first object found
        first_object = response["Contents"][0]["Key"]
        tag_response = s3_client.get_object_tagging(Bucket=s3_bucket, Key=first_object)

        return {tag["Key"]: tag["Value"] for tag in tag_response.get("TagSet", [])}
    except Exception:
        return {}


def tag_objects_in_prefix(
    s3_client, s3_bucket: str, prefix: str, tags: dict, dry_run: bool = True
) -> bool:
    """Apply tags to all objects under a prefix"""
    if dry_run:
        logger.info(f"DRY RUN: Would tag objects in {prefix} with {tags}")
        return True

    try:
        paginator = s3_client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(Bucket=s3_bucket, Prefix=prefix + "/")

        objects_tagged = 0
        tag_set = [{"Key": k, "Value": v} for k, v in tags.items()]

        for page in page_iterator:
            for obj in page.get("Contents", []):
                try:
                    s3_client.put_object_tagging(
                        Bucket=s3_bucket, Key=obj["Key"], Tagging={"TagSet": tag_set}
                    )
                    objects_tagged += 1
                except Exception as e:
                    logger.warning(f"Failed to tag {obj['Key']}: {e}")

        logger.info(f"Tagged {objects_tagged} objects in {prefix}")
        return True
    except Exception as e:
        logger.error(f"Failed to tag objects in {prefix}: {e}")
        return False


def delete_objects_in_prefix(
    s3_client,
    s3_bucket: str,
    prefix: str,
    dry_run: bool = True,
    enable_deletion: bool = False,
) -> bool:
    """Delete all objects under a prefix (if deletion is enabled)"""
    if not enable_deletion:
        logger.info(f"Deletion not enabled - would delete objects in {prefix}")
        return False

    if dry_run:
        logger.info(f"DRY RUN: Would delete objects in {prefix}")
        return True

    try:
        paginator = s3_client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(Bucket=s3_bucket, Prefix=prefix + "/")

        objects_deleted = 0

        for page in page_iterator:
            if "Contents" in page:
                # Delete objects in batches
                delete_keys = [{"Key": obj["Key"]} for obj in page["Contents"]]
                if delete_keys:
                    s3_client.delete_objects(
                        Bucket=s3_bucket, Delete={"Objects": delete_keys}
                    )
                    objects_deleted += len(delete_keys)

        logger.info(f"Deleted {objects_deleted} objects in {prefix}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete objects in {prefix}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Tag S3 results directories")
    parser.add_argument(
        "--bucket", default="nf-core-awsmegatests", help="S3 bucket name"
    )
    parser.add_argument(
        "--pipelines-json-url",
        default="https://nf-core.s3.amazonaws.com/pipelines.json",
        help="URL to pipelines.json",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Dry run mode (default: True)",
    )
    parser.add_argument("--live", action="store_true", help="Disable dry run mode")
    parser.add_argument(
        "--enable-deletion",
        action="store_true",
        help="Enable deletion of orphaned directories (DANGEROUS)",
    )

    args = parser.parse_args()

    # Handle dry run logic
    dry_run = args.dry_run and not args.live

    # Configuration
    s3_bucket = args.bucket
    pipelines_json_url = args.pipelines_json_url
    enable_deletion = args.enable_deletion

    logger.info("Starting S3 results tagging job")
    logger.info(f"Bucket: {s3_bucket}")
    logger.info(f"Dry run mode: {dry_run}")
    logger.info(f"Deletion enabled: {enable_deletion}")

    # Fetch current pipeline data
    current_releases = fetch_pipeline_data(pipelines_json_url)

    # List all results directories in S3
    s3_results_dirs = list_s3_results_directories(s3_bucket)

    # Initialize S3 client
    s3_client = boto3.client("s3")

    # Statistics
    stats = {
        "current_tagged": 0,
        "orphaned_tagged": 0,
        "orphaned_deleted": 0,
        "errors": 0,
    }

    logger.info("Starting tagging analysis...")

    for results_dir in s3_results_dirs:
        try:
            logger.info(f"Processing: {results_dir}")

            # Check if this is a current release
            if results_dir in current_releases:
                # Current release - tag as active
                release_info = current_releases[results_dir]
                tags = {
                    "pipeline": release_info["pipeline"],
                    "release": release_info["version"],
                    "sha": release_info["sha"],
                    "status": "current",
                    "tagged_date": datetime.utcnow().isoformat(),
                    "tagged_by": "nf-core-ops-automation",
                }

                if tag_objects_in_prefix(
                    s3_client, s3_bucket, results_dir, tags, dry_run
                ):
                    stats["current_tagged"] += 1
                    logger.info(f"✅ Tagged current release: {results_dir}")
                else:
                    stats["errors"] += 1

            else:
                # Orphaned directory - tag for deletion
                pipeline_name = results_dir.split("/")[0]
                tags = {
                    "pipeline": pipeline_name,
                    "status": "orphaned",
                    "deleteme": "true",
                    "tagged_date": datetime.utcnow().isoformat(),
                    "tagged_by": "nf-core-ops-automation",
                }

                if tag_objects_in_prefix(
                    s3_client, s3_bucket, results_dir, tags, dry_run
                ):
                    stats["orphaned_tagged"] += 1
                    logger.warning(f"🗑️  Tagged orphaned directory: {results_dir}")

                    # Optionally delete if enabled
                    if enable_deletion:
                        if delete_objects_in_prefix(
                            s3_client, s3_bucket, results_dir, dry_run, enable_deletion
                        ):
                            stats["orphaned_deleted"] += 1
                else:
                    stats["errors"] += 1

        except Exception as e:
            logger.error(f"Error processing {results_dir}: {e}")
            stats["errors"] += 1

    # Print final summary
    logger.info("=" * 60)
    logger.info("S3 RESULTS TAGGING SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Current releases tagged: {stats['current_tagged']}")
    logger.info(f"Orphaned directories tagged: {stats['orphaned_tagged']}")
    if enable_deletion:
        logger.info(f"Orphaned directories deleted: {stats['orphaned_deleted']}")
    logger.info(f"Errors encountered: {stats['errors']}")
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    logger.info("=" * 60)

    # Exit with error code if there were significant issues
    if stats["errors"] > len(s3_results_dirs) * 0.1:  # More than 10% errors
        logger.error("Too many errors encountered - check configuration")
        sys.exit(1)

    logger.info("S3 results tagging completed successfully")


if __name__ == "__main__":
    main()
