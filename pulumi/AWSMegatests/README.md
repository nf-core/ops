```sh
pulumi env run nf-core/AWSMegatests-dev -i pulumi import aws:s3/bucket:Bucket awsmegatests-bucket nf-core-awsmegatests
# pulumi env run nf-core/AWSMegatests-dev -i pulumi import aws:s3/bucketAclV2:BucketAclV2 awsmegatests-bucket-acl nf-core-awsmegatests
pulumi env run nf-core/AWSMegatests-dev -i pulumi import aws:s3/bucketPolicy:BucketPolicy megatests-bucket-policy nf-core-awsmegatests
```
