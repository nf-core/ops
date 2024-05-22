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
