# Pulumi AWS Provider Guide

Quick reference for common AWS resources and patterns in Pulumi.

## Table of Contents

- [Authentication](#authentication)
- [Common Resources](#common-resources)
- [IAM and Security](#iam-and-security)
- [Networking](#networking)
- [Storage](#storage)
- [Compute](#compute)
- [Best Practices](#best-practices)

## Authentication

### Using Environment Variables

```bash
# Set via .envrc (recommended with 1Password)
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_REGION="us-east-1"
```

### Configure Provider

```python
import pulumi_aws as aws

# Use default credentials
# (from environment or AWS CLI config)

# Or explicit configuration
provider = aws.Provider("custom",
    region="us-east-1",
    access_key="key",
    secret_key="secret",
)
```

### Multiple Regions

```python
# Primary region
bucket_east = aws.s3.Bucket("east")

# Secondary region provider
provider_west = aws.Provider("west", region="us-west-2")
bucket_west = aws.s3.Bucket("west",
    opts=pulumi.ResourceOptions(provider=provider_west)
)
```

## Common Resources

### S3 Bucket

```python
import pulumi_aws as aws

bucket = aws.s3.Bucket(
    "my-bucket",
    bucket="unique-bucket-name",
    acl="private",
    versioning=aws.s3.BucketVersioningArgs(
        enabled=True,
    ),
    server_side_encryption_configuration=aws.s3.BucketServerSideEncryptionConfigurationArgs(
        rule=aws.s3.BucketServerSideEncryptionConfigurationRuleArgs(
            apply_server_side_encryption_by_default=aws.s3.BucketServerSideEncryptionConfigurationRuleApplyServerSideEncryptionByDefaultArgs(
                sse_algorithm="AES256",
            ),
        ),
    ),
    tags={
        "Environment": pulumi.get_stack(),
    },
)

# Block public access
aws.s3.BucketPublicAccessBlock(
    "block-public",
    bucket=bucket.id,
    block_public_acls=True,
    block_public_policy=True,
    ignore_public_acls=True,
    restrict_public_buckets=True,
)

pulumi.export("bucket_name", bucket.id)
pulumi.export("bucket_arn", bucket.arn)
```

### Lambda Function

```python
import pulumi_aws as aws

# IAM role for Lambda
role = aws.iam.Role(
    "lambda-role",
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }""",
)

# Attach basic execution policy
aws.iam.RolePolicyAttachment(
    "lambda-execution",
    role=role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
)

# Lambda function
function = aws.lambda_.Function(
    "my-function",
    runtime="python3.11",
    handler="index.handler",
    role=role.arn,
    code=pulumi.AssetArchive({
        ".": pulumi.FileArchive("./lambda"),
    }),
    environment=aws.lambda_.FunctionEnvironmentArgs(
        variables={
            "KEY": "value",
        },
    ),
)

pulumi.export("function_name", function.name)
pulumi.export("function_arn", function.arn)
```

### EC2 Instance

```python
import pulumi_aws as aws

# Get latest Amazon Linux AMI
ami = aws.ec2.get_ami(
    most_recent=True,
    owners=["amazon"],
    filters=[
        aws.ec2.GetAmiFilterArgs(
            name="name",
            values=["amzn2-ami-hvm-*-x86_64-gp2"],
        ),
    ],
)

# Security group
sg = aws.ec2.SecurityGroup(
    "web-sg",
    description="Allow HTTP",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=80,
            to_port=80,
            cidr_blocks=["0.0.0.0/0"],
        ),
    ],
)

# Instance
instance = aws.ec2.Instance(
    "web-server",
    instance_type="t3.micro",
    ami=ami.id,
    vpc_security_group_ids=[sg.id],
    tags={
        "Name": "WebServer",
    },
)

pulumi.export("instance_id", instance.id)
pulumi.export("public_ip", instance.public_ip)
```

## IAM and Security

### IAM User with Policy

```python
import pulumi_aws as aws
import json

# IAM user
user = aws.iam.User(
    "ci-user",
    name="my-ci-user",
    tags={
        "Purpose": "CI/CD",
    },
)

# Access key
access_key = aws.iam.AccessKey(
    "ci-key",
    user=user.name,
)

# IAM policy
policy_document = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Action": [
            "s3:PutObject",
            "s3:GetObject",
        ],
        "Resource": "arn:aws:s3:::my-bucket/*",
    }],
}

policy = aws.iam.Policy(
    "ci-policy",
    policy=json.dumps(policy_document),
    description="CI/CD bucket access",
)

# Attach policy to user
aws.iam.UserPolicyAttachment(
    "ci-attach",
    user=user.name,
    policy_arn=policy.arn,
)

pulumi.export("user_name", user.name)
pulumi.export("access_key_id", access_key.id)
pulumi.export("access_key_secret", access_key.secret)
```

### Security Group with Rules

```python
import pulumi_aws as aws

sg = aws.ec2.SecurityGroup(
    "app-sg",
    description="Application security group",
    vpc_id=vpc.id,
)

# SSH access
aws.ec2.SecurityGroupRule(
    "ssh",
    type="ingress",
    security_group_id=sg.id,
    protocol="tcp",
    from_port=22,
    to_port=22,
    cidr_blocks=["10.0.0.0/8"],
)

# HTTP access
aws.ec2.SecurityGroupRule(
    "http",
    type="ingress",
    security_group_id=sg.id,
    protocol="tcp",
    from_port=80,
    to_port=80,
    cidr_blocks=["0.0.0.0/0"],
)

# Egress (all traffic)
aws.ec2.SecurityGroupRule(
    "egress",
    type="egress",
    security_group_id=sg.id,
    protocol="-1",
    from_port=0,
    to_port=0,
    cidr_blocks=["0.0.0.0/0"],
)
```

## Networking

### VPC with Subnets

```python
import pulumi_aws as aws

# VPC
vpc = aws.ec2.Vpc(
    "main",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={"Name": "main-vpc"},
)

# Internet Gateway
igw = aws.ec2.InternetGateway(
    "igw",
    vpc_id=vpc.id,
    tags={"Name": "main-igw"},
)

# Public subnet
public_subnet = aws.ec2.Subnet(
    "public",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone="us-east-1a",
    map_public_ip_on_launch=True,
    tags={"Name": "public-subnet"},
)

# Route table for public subnet
public_rt = aws.ec2.RouteTable(
    "public-rt",
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            gateway_id=igw.id,
        ),
    ],
    tags={"Name": "public-rt"},
)

# Associate route table with subnet
aws.ec2.RouteTableAssociation(
    "public-rta",
    subnet_id=public_subnet.id,
    route_table_id=public_rt.id,
)

pulumi.export("vpc_id", vpc.id)
pulumi.export("public_subnet_id", public_subnet.id)
```

## Storage

### RDS Database

```python
import pulumi_aws as aws

# DB subnet group
db_subnet_group = aws.rds.SubnetGroup(
    "db-subnets",
    subnet_ids=[subnet1.id, subnet2.id],
    tags={"Name": "DB subnets"},
)

# DB instance
db = aws.rds.Instance(
    "postgres",
    engine="postgres",
    engine_version="14.7",
    instance_class="db.t3.micro",
    allocated_storage=20,
    db_name="mydb",
    username="admin",
    password=config.require_secret("db_password"),
    db_subnet_group_name=db_subnet_group.name,
    vpc_security_group_ids=[db_sg.id],
    skip_final_snapshot=True,
    tags={"Name": "postgres-db"},
)

pulumi.export("db_endpoint", db.endpoint)
pulumi.export("db_name", db.db_name)
```

## Compute

### ECS Service

```python
import pulumi_aws as aws

# ECS Cluster
cluster = aws.ecs.Cluster(
    "app-cluster",
    name="app-cluster",
)

# Task definition
task_definition = aws.ecs.TaskDefinition(
    "app-task",
    family="app",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    cpu="256",
    memory="512",
    container_definitions=pulumi.Output.json_dumps([{
        "name": "app",
        "image": "nginx:latest",
        "portMappings": [{
            "containerPort": 80,
            "protocol": "tcp",
        }],
    }]),
)

# ECS Service
service = aws.ecs.Service(
    "app-service",
    cluster=cluster.arn,
    task_definition=task_definition.arn,
    desired_count=2,
    launch_type="FARGATE",
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
        subnets=[subnet.id],
        security_groups=[sg.id],
        assign_public_ip=True,
    ),
)

pulumi.export("cluster_name", cluster.name)
```

## Best Practices

### Tagging Strategy

```python
import pulumi

# Define common tags
common_tags = {
    "Project": pulumi.get_project(),
    "Environment": pulumi.get_stack(),
    "ManagedBy": "Pulumi",
}

# Apply to resources
resource = aws.Resource(
    "name",
    tags={**common_tags, "Component": "specific"},
)
```

### Resource Naming

```python
import pulumi

stack = pulumi.get_stack()
project = pulumi.get_project()

# Include stack in names
bucket = aws.s3.Bucket(
    "data-bucket",
    bucket=f"{project}-data-{stack}",
)

# Use logical names for resources
instance = aws.ec2.Instance(
    "web-server",  # Logical name
    tags={"Name": f"{project}-web-{stack}"},  # Display name
)
```

### Security Defaults

```python
# Always block public access for S3
aws.s3.BucketPublicAccessBlock(
    "block-public",
    bucket=bucket.id,
    block_public_acls=True,
    block_public_policy=True,
    ignore_public_acls=True,
    restrict_public_buckets=True,
)

# Enable encryption by default
server_side_encryption_configuration=aws.s3.BucketServerSideEncryptionConfigurationArgs(
    rule=aws.s3.BucketServerSideEncryptionConfigurationRuleArgs(
        apply_server_side_encryption_by_default=aws.s3.BucketServerSideEncryptionConfigurationRuleApplyServerSideEncryptionByDefaultArgs(
            sse_algorithm="AES256",
        ),
    ),
)

# Use private ACLs
acl="private"
```

## Common Patterns

### Using Data Sources

```python
# Get current AWS account
current = aws.get_caller_identity()
account_id = current.account_id

# Get current region
region = aws.get_region()

# Get existing VPC
vpc = aws.ec2.get_vpc(default=True)

# Use in resources
bucket = aws.s3.Bucket(
    "account-bucket",
    bucket=f"my-bucket-{account_id}",
)
```

### Conditional Resources

```python
import pulumi

stack = pulumi.get_stack()

# Only create in production
if stack == "production":
    monitoring = aws.cloudwatch.MetricAlarm(...)
```

## Documentation Links

- **AWS Provider**: https://www.pulumi.com/registry/packages/aws/
- **API Reference**: https://www.pulumi.com/registry/packages/aws/api-docs/
- **Examples**: https://github.com/pulumi/examples/tree/master/aws-py-*
