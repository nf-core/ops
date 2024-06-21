https://eu-west-1.console.aws.amazon.com/cloudwatch/home?region=eu-west-1#logsV2:log-groups/log-group/$252Fsentieon$252Flicsrvr$252FLicsrvrLog

https://support.sentieon.com/versions/202112.07/appnotes/aws_deployment/#deployment-of-the-sentieon-reg-license-server
Got rid of the Terraform thing because Don said it may not be relevant.

importing Maxine stuff and then just gonna pull it all in and just create EC2 instance manually.

```sh
pulumi env run nf-core/AWSMegatests-dev -i pulumi import aws:ec2/vpc:Vpc sentieon-vpc vpc-09544162c32f4affc
```
