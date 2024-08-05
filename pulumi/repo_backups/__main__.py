import pulumi
import pulumi_aws as aws

# Create an S3 bucket
bucket = aws.s3.Bucket("my_bucket")

# Add a lifecycle rule to delete files after 1 year
one_year = 365  # days in a year
bucket_lifecycle_policy = aws.s3.BucketLifecycleConfiguration(
    "my_bucket_lifecycle_policy",
    bucket=bucket.id,
    rules=[
        aws.s3.BucketLifecycleConfigurationRuleArgs(
            id="expireAfterOneYear",
            enabled=True,
            expiration=aws.s3.BucketLifecycleConfigurationRuleExpirationArgs(
                days=one_year,
            ),
        )
    ],
)

# Export the name of the bucket
pulumi.export("bucket_name", bucket.id)  # type: ignore[attr-defined]
