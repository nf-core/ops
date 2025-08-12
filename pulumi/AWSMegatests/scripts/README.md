# AWS Megatests Utility Scripts

This directory contains utility scripts for AWS Megatests infrastructure management.

## Log File Tagging Script

**Purpose**: One-time batch job to tag existing log files in S3 work directories for preservation during lifecycle cleanup.

### Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Dry run to see what would be tagged
python tag_existing_log_files.py --bucket nf-core-awsmegatests --dry-run

# Actually tag the files
python tag_existing_log_files.py --bucket nf-core-awsmegatests

# With custom threading (default is 10 workers)
python tag_existing_log_files.py --bucket nf-core-awsmegatests --max-workers 20
```

### Prerequisites

- AWS credentials configured (AWS CLI, IAM role, or environment variables)
- S3 permissions: `s3:ListBucket`, `s3:GetObjectTagging`, `s3:PutObjectTagging`

### What it does

1. Scans the `work/` directory for log files matching Nextflow patterns
2. Tags log files with `nextflow.io/metadata=true`
3. Preserves existing tags while adding the metadata tag
4. Uses multi-threading for performance with large buckets

### Log File Patterns

The script identifies these Nextflow log files:

- `.command.log` - Main command log
- `.command.err` - Error log
- `.command.out` - Standard output
- `.exitcode` - Exit code file
- `.command.sh` - Command script
- `.command.run` - Run script
- `.command.begin` - Begin timestamp
- `trace.txt` - Trace file
- `timeline.html` - Timeline report
- `report.html` - Execution report
- `dag.html` - DAG visualization

### Integration with Lifecycle Rules

Tagged files are preserved by S3 lifecycle rules:

- Tagged log files: Kept for 90 days, then moved to cheaper storage classes
- Untagged work files: Deleted after 14 days for aggressive cleanup
- Future log files will be tagged automatically by Nextflow (no need to run this script again)
