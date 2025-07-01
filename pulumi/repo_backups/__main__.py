import pulumi
import pulumi_aws as aws

# Create an S3 bucket using the V2 API
bucket = aws.s3.BucketV2("my_bucket")

# Add a lifecycle rule to delete files after 1 year
one_year = 365  # days in a year
bucket_lifecycle_policy = aws.s3.BucketLifecycleConfigurationV2(
    "my_bucket_lifecycle_policy",
    bucket=bucket.id,
    rules=[
        aws.s3.BucketLifecycleConfigurationV2RuleArgs(
            id="expireAfterOneYear",
            status="Enabled",
            expiration=aws.s3.BucketLifecycleConfigurationV2RuleExpirationArgs(
                days=one_year,
            ),
        )
    ],
)

# Export the name of the bucket
pulumi.export("bucket_name", bucket.id)
