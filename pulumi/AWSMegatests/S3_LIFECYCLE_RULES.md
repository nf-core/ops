# S3 Lifecycle Rules for nf-core-awsmegatests

## Overview

This document describes the S3 lifecycle rules needed for the `nf-core-awsmegatests` bucket to automatically clean up `work/` and `scratch/` directories while preserving log files.

## Required Permissions

To apply these lifecycle rules, you need AWS credentials with the following permission:

- `s3:PutLifecycleConfiguration` on `arn:aws:s3:::nf-core-awsmegatests`

## Lifecycle Rules Configuration

### Current Issue

The Pulumi deployment failed with:

```
User: arn:aws:iam::728131696474:user/tower-awstest is not authorized to perform: s3:PutLifecycleConfiguration
```

### Required Rules

The following lifecycle rules should be applied to the `nf-core-awsmegatests` S3 bucket:

#### Rule 1: Preserve Metadata Files (Existing)

- **ID**: `preserve-metadata-files`
- **Filter**: Tag `nextflow.io/metadata=true`
- **Action**: Transition to IA (30 days) → Glacier (90 days), no expiration

#### Rule 2: Cleanup Temporary Files (Existing)

- **ID**: `cleanup-temporary-files`
- **Filter**: Tag `nextflow.io/temporary=true`
- **Action**: Delete after 30 days

#### Rule 3: Preserve Log Files in Work Directory (New)

- **ID**: `preserve-work-log-files`
- **Filter**: Prefix `work/` AND tag `nextflow.io/log=true`
- **Action**: Transition to IA (30 days) → Glacier (180 days), no expiration

#### Rule 4: Preserve Log Files in Scratch Directory (New)

- **ID**: `preserve-scratch-log-files`
- **Filter**: Prefix `scratch/` AND tag `nextflow.io/log=true`
- **Action**: Transition to IA (30 days) → Glacier (180 days), no expiration

#### Rule 5: Cleanup Non-Log Files in Work Directory (Updated)

- **ID**: `cleanup-work-directory`
- **Filter**: Prefix `work/`
- **Action**: Delete after 30 days (reduced from 90 days)

#### Rule 6: Cleanup Non-Log Files in Scratch Directory (New)

- **ID**: `cleanup-scratch-directory`
- **Filter**: Prefix `scratch/`
- **Action**: Delete after 30 days

#### Rule 7: Cleanup Incomplete Multipart Uploads (Existing)

- **ID**: `cleanup-incomplete-multipart-uploads`
- **Action**: Abort incomplete uploads after 7 days

## Manual Application via AWS CLI

If you have AWS credentials with the necessary permissions, you can apply these rules using the AWS CLI:

```bash
# Create lifecycle configuration JSON file
cat > lifecycle-config.json << 'EOF'
{
    "Rules": [
        {
            "ID": "preserve-metadata-files",
            "Status": "Enabled",
            "Filter": {
                "Tag": {
                    "Key": "nextflow.io/metadata",
                    "Value": "true"
                }
            },
            "Transitions": [
                {
                    "Days": 30,
                    "StorageClass": "STANDARD_IA"
                },
                {
                    "Days": 90,
                    "StorageClass": "GLACIER"
                }
            ]
        },
        {
            "ID": "cleanup-temporary-files",
            "Status": "Enabled",
            "Filter": {
                "Tag": {
                    "Key": "nextflow.io/temporary",
                    "Value": "true"
                }
            },
            "Expiration": {
                "Days": 30
            }
        },
        {
            "ID": "preserve-work-log-files",
            "Status": "Enabled",
            "Filter": {
                "And": {
                    "Prefix": "work/",
                    "Tags": [
                        {
                            "Key": "nextflow.io/log",
                            "Value": "true"
                        }
                    ]
                }
            },
            "Transitions": [
                {
                    "Days": 30,
                    "StorageClass": "STANDARD_IA"
                },
                {
                    "Days": 180,
                    "StorageClass": "GLACIER"
                }
            ]
        },
        {
            "ID": "preserve-scratch-log-files",
            "Status": "Enabled",
            "Filter": {
                "And": {
                    "Prefix": "scratch/",
                    "Tags": [
                        {
                            "Key": "nextflow.io/log",
                            "Value": "true"
                        }
                    ]
                }
            },
            "Transitions": [
                {
                    "Days": 30,
                    "StorageClass": "STANDARD_IA"
                },
                {
                    "Days": 180,
                    "StorageClass": "GLACIER"
                }
            ]
        },
        {
            "ID": "cleanup-work-directory",
            "Status": "Enabled",
            "Filter": {
                "Prefix": "work/"
            },
            "Expiration": {
                "Days": 30
            }
        },
        {
            "ID": "cleanup-scratch-directory",
            "Status": "Enabled",
            "Filter": {
                "Prefix": "scratch/"
            },
            "Expiration": {
                "Days": 30
            }
        },
        {
            "ID": "cleanup-incomplete-multipart-uploads",
            "Status": "Enabled",
            "AbortIncompleteMultipartUpload": {
                "DaysAfterInitiation": 7
            }
        }
    ]
}
EOF

# Apply the lifecycle configuration
aws s3api put-bucket-lifecycle-configuration \
    --bucket nf-core-awsmegatests \
    --lifecycle-configuration file://lifecycle-config.json
```

## Nextflow Configuration Requirements

To ensure log files are properly preserved, Nextflow pipelines need to tag log files with `nextflow.io/log=true`. This can be configured in the Nextflow configuration:

```groovy
// nextflow.config
aws {
    s3 {
        // Enable object tagging for log files
        tags {
            'nextflow.io/log' = { task.workDir.name.contains('.command.log') || task.workDir.name.contains('.command.out') || task.workDir.name.contains('.command.err') ? 'true' : null }
        }
    }
}
```

## Summary

**What This Achieves:**

- ✅ Files in `work/` and `scratch/` directories are automatically deleted after 30 days
- ✅ Log files (tagged with `nextflow.io/log=true`) are preserved indefinitely
- ✅ Log files are moved to cheaper storage tiers (IA after 30 days, Glacier after 180 days)
- ✅ Incomplete multipart uploads are cleaned up automatically
- ✅ Metadata files continue to be preserved indefinitely

**Next Steps:**

1. Apply the lifecycle configuration using AWS CLI with appropriate credentials
2. Configure Nextflow pipelines to tag log files appropriately
3. Monitor S3 costs and adjust retention periods if needed

## Troubleshooting

**Permission Denied Error:**

- The AWS credentials must have `s3:PutLifecycleConfiguration` permission
- Consider using AWS admin credentials temporarily to apply the configuration
- Once applied, the rules will execute automatically using AWS's built-in lifecycle management

**Log Files Not Preserved:**

- Verify that Nextflow is properly tagging log files with `nextflow.io/log=true`
- Check S3 object tags using: `aws s3api get-object-tagging --bucket nf-core-awsmegatests --key work/some/path/.command.log`
