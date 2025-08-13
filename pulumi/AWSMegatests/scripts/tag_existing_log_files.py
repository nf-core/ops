#!/usr/bin/env python3
"""
One-time batch job to tag existing log files in S3 work directories.

This script identifies and tags log files with nextflow.io/metadata=true
to preserve them during lifecycle cleanup, while allowing other files
to be cleaned up more aggressively (14 days vs 90 days for tagged files).

Usage:
    python tag_existing_log_files.py --bucket nf-core-awsmegatests [--dry-run]

Requirements:
    - AWS credentials configured (via AWS CLI, IAM role, or environment variables)
    - S3 permissions: s3:ListBucket, s3:GetObjectTagging, s3:PutObjectTagging
"""

import argparse
import boto3
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from botocore.exceptions import ClientError, NoCredentialsError
from typing import List, Dict, Tuple
import re
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("tag_log_files.log"),
    ],
)
logger = logging.getLogger(__name__)

# Log file patterns for Nextflow work directories
LOG_FILE_PATTERNS = [
    r"\.command\.log$",  # Main command log
    r"\.command\.err$",  # Error log
    r"\.command\.out$",  # Standard output
    r"\.exitcode$",  # Exit code file
    r"\.command\.sh$",  # Command script
    r"\.command\.run$",  # Run script
    r"\.command\.begin$",  # Begin timestamp
    r"trace\.txt$",  # Trace file
    r"timeline\.html$",  # Timeline report
    r"report\.html$",  # Execution report
    r"dag\.html$",  # DAG visualization
]

# Compile regex patterns for performance
COMPILED_PATTERNS = [
    re.compile(pattern, re.IGNORECASE) for pattern in LOG_FILE_PATTERNS
]

# Nextflow metadata tag
METADATA_TAG = {"nextflow.io/metadata": "true"}


def is_log_file(key: str) -> bool:
    """Check if an S3 object key matches log file patterns.

    Args:
        key: S3 object key

    Returns:
        bool: True if key matches log file patterns
    """
    # Extract filename from key
    filename = key.split("/")[-1]

    # Check against compiled patterns
    return any(pattern.search(filename) for pattern in COMPILED_PATTERNS)


def get_s3_client():
    """Create and configure S3 client with error handling."""
    try:
        client = boto3.client("s3")
        # Test credentials by listing buckets
        client.list_buckets()
        return client
    except NoCredentialsError:
        logger.error("AWS credentials not found. Please configure AWS credentials.")
        sys.exit(1)
    except ClientError as e:
        logger.error(f"AWS client error: {e}")
        sys.exit(1)


def list_work_directory_objects(s3_client, bucket_name: str) -> List[Dict]:
    """List all objects in work/ directories that match log file patterns.

    Args:
        s3_client: Boto3 S3 client
        bucket_name: S3 bucket name

    Returns:
        List of object dictionaries for log files
    """
    log_objects = []
    paginator = s3_client.get_paginator("list_objects_v2")

    logger.info("Scanning work/ directory for log files...")

    try:
        # List objects with work/ prefix
        page_iterator = paginator.paginate(
            Bucket=bucket_name, Prefix="work/", PaginationConfig={"PageSize": 1000}
        )

        total_objects = 0
        for page in page_iterator:
            if "Contents" in page:
                for obj in page["Contents"]:
                    total_objects += 1
                    if is_log_file(obj["Key"]):
                        log_objects.append(obj)

                    # Progress update every 10k objects
                    if total_objects % 10000 == 0:
                        logger.info(
                            f"Scanned {total_objects} objects, found {len(log_objects)} log files"
                        )

        logger.info(
            f"Scan complete: {len(log_objects)} log files found in {total_objects} total objects"
        )

    except ClientError as e:
        logger.error(f"Error listing objects: {e}")
        raise

    return log_objects


def get_object_tags(s3_client, bucket_name: str, key: str) -> Dict[str, str]:
    """Get existing tags for an S3 object.

    Args:
        s3_client: Boto3 S3 client
        bucket_name: S3 bucket name
        key: S3 object key

    Returns:
        Dictionary of existing tags
    """
    try:
        response = s3_client.get_object_tagging(Bucket=bucket_name, Key=key)
        return {tag["Key"]: tag["Value"] for tag in response.get("TagSet", [])}
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            logger.warning(f"Object not found: {key}")
            return {}
        else:
            logger.error(f"Error getting tags for {key}: {e}")
            raise


def tag_log_file(
    s3_client, bucket_name: str, key: str, dry_run: bool = False
) -> Tuple[bool, str]:
    """Tag a single log file with metadata tag.

    Args:
        s3_client: Boto3 S3 client
        bucket_name: S3 bucket name
        key: S3 object key
        dry_run: If True, don't actually apply tags

    Returns:
        Tuple of (success, message)
    """
    try:
        # Get existing tags
        existing_tags = get_object_tags(s3_client, bucket_name, key)

        # Check if already tagged
        if METADATA_TAG["nextflow.io/metadata"] in existing_tags.values():
            return True, "Already tagged"

        # Merge with existing tags
        new_tags = {**existing_tags, **METADATA_TAG}

        if dry_run:
            return True, f"Would tag with: {new_tags}"

        # Apply tags
        tag_set = [{"Key": k, "Value": v} for k, v in new_tags.items()]
        s3_client.put_object_tagging(
            Bucket=bucket_name, Key=key, Tagging={"TagSet": tag_set}
        )

        return True, "Tagged successfully"

    except ClientError as e:
        return False, f"Error: {e}"


def process_log_files_batch(
    s3_client,
    bucket_name: str,
    log_objects: List[Dict],
    dry_run: bool = False,
    max_workers: int = 10,
) -> Dict[str, int]:
    """Process log files in batches with threading.

    Args:
        s3_client: Boto3 S3 client
        bucket_name: S3 bucket name
        log_objects: List of log file objects
        dry_run: If True, don't actually apply tags
        max_workers: Maximum number of worker threads

    Returns:
        Dictionary with processing statistics
    """
    stats = {"processed": 0, "tagged": 0, "already_tagged": 0, "errors": 0}

    logger.info(
        f"Processing {len(log_objects)} log files with {max_workers} workers..."
    )

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all jobs
        future_to_key = {
            executor.submit(
                tag_log_file, s3_client, bucket_name, obj["Key"], dry_run
            ): obj["Key"]
            for obj in log_objects
        }

        # Process results
        for future in as_completed(future_to_key):
            key = future_to_key[future]
            stats["processed"] += 1

            try:
                success, message = future.result()
                if success:
                    if "Already tagged" in message:
                        stats["already_tagged"] += 1
                    else:
                        stats["tagged"] += 1

                    if stats["processed"] % 100 == 0:
                        logger.info(
                            f"Processed {stats['processed']}/{len(log_objects)} files"
                        )
                else:
                    stats["errors"] += 1
                    logger.error(f"Failed to tag {key}: {message}")

            except Exception as e:
                stats["errors"] += 1
                logger.error(f"Exception processing {key}: {e}")

    return stats


def main():
    """Main function to orchestrate log file tagging."""
    parser = argparse.ArgumentParser(
        description="Tag existing log files in S3 work directories"
    )
    parser.add_argument(
        "--bucket", required=True, help="S3 bucket name (e.g., nf-core-awsmegatests)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be tagged without actually tagging",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=10,
        help="Maximum number of worker threads (default: 10)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info(f"Starting log file tagging for bucket: {args.bucket}")
    if args.dry_run:
        logger.info("DRY RUN MODE - No actual changes will be made")

    # Initialize S3 client
    s3_client = get_s3_client()

    # List log files in work directories
    start_time = time.time()
    log_objects = list_work_directory_objects(s3_client, args.bucket)
    scan_time = time.time() - start_time

    if not log_objects:
        logger.info("No log files found to tag")
        return

    logger.info(
        f"Found {len(log_objects)} log files to process (scan took {scan_time:.2f}s)"
    )

    # Process log files
    process_start = time.time()
    stats = process_log_files_batch(
        s3_client, args.bucket, log_objects, args.dry_run, args.max_workers
    )
    process_time = time.time() - process_start

    # Print summary
    logger.info("=" * 60)
    logger.info("TAGGING SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total files processed: {stats['processed']}")
    logger.info(f"Files newly tagged: {stats['tagged']}")
    logger.info(f"Files already tagged: {stats['already_tagged']}")
    logger.info(f"Errors encountered: {stats['errors']}")
    logger.info(f"Processing time: {process_time:.2f}s")
    logger.info(f"Total time: {(scan_time + process_time):.2f}s")

    if args.dry_run:
        logger.info("\nThis was a DRY RUN - no actual changes were made")
        logger.info("Run without --dry-run to apply tags")

    if stats["errors"] > 0:
        logger.warning(f"{stats['errors']} errors occurred - check logs for details")
        sys.exit(1)


if __name__ == "__main__":
    main()
