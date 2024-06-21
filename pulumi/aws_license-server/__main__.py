import pulumi
import pulumi_aws as aws

sentieon_vpc = aws.ec2.Vpc(
    "sentieon-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    instance_tenancy="default",
    tags={
        "DELETE_ME": "",
        "Name": "sentieon_test_license_server_vpc",
    },
    opts=pulumi.ResourceOptions(protect=True),
)
