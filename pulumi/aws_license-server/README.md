Pulumi script converted from Terraform script for AWS License Server

- https://www.pulumi.com/docs/using-pulumi/adopting-pulumi/migrating-to-pulumi/from-terraform/
- https://github.com/Sentieon/terraform/blob/master/aws_license-server/main.tf
- https://www.pulumi.com/docs/install/

```bash
# install Pulumi
brew install pulumi/tap/pulumi

# make a new conda env to install the Python plugin into
conda create -n pulumi_py python

conda activate pulumi_py

pip3 install pulumi_terraform

# download copy of this repo https://github.com/Sentieon/terraform/tree/master/aws_license-server
# cd into aws_license-server dir

# do the conversion
pulumi convert --from terraform --language python
```

## Manually created a "stack"

```bash
cd pulumi/aws_license-server
pulumi stack
```

# Importing old Sentieon Infra

https://eu-west-1.console.aws.amazon.com/cloudwatch/home?region=eu-west-1#logsV2:log-groups/log-group/$252Fsentieon$252Flicsrvr$252FLicsrvrLog

https://support.sentieon.com/versions/202112.07/appnotes/aws_deployment/#deployment-of-the-sentieon-reg-license-server
Got rid of the Terraform thing because Don said it may not be relevant.

importing Maxine stuff and then just gonna pull it all in and just create EC2 instance manually.

```sh
pulumi env run nf-core/AWSMegatests-dev -i pulumi import aws:ec2/vpc:Vpc sentieon-vpc vpc-09544162c32f4affc
pulumi env run nf-core/AWSMegatests-dev -i pulumi import aws:ec2/securityGroup:SecurityGroup license-server sg-0050bb55ca1c6292c
```
