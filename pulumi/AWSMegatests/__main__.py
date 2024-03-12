import pulumi
import pulumi_aws as aws

# Pull in the existing AWS VPC named 'example-vpc'
vpc = aws.ec2.Vpc.get("existing-vpc", "example-vpc")

# Pull in the existing AWS Subnet named 'example-subnet'
subnet = aws.ec2.Subnet.get("existing-subnet", "example-subnet", vpc_id=vpc.id)

# Pull in the existing AWS Security Group named 'example-sg'
security_group = aws.ec2.SecurityGroup.get("existing-sg", "example-sg")

# Pull in the existing AWS EC2 Key Pair named 'example-key-pair'
key_pair = aws.ec2.KeyPair.get("existing-key-pair", "example-key-pair")

# Export the IDs of the pulled resources
pulumi.export("vpc_id", vpc.id)
pulumi.export("subnet_id", subnet.id)
pulumi.export("security_group_id", security_group.id)
pulumi.export("key_pair_id", key_pair.id)