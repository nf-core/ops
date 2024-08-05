import pulumi
import pulumi_aws as aws

# Create the VPC
vpc = aws.ec2.Vpc(
    "plausible-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_support=True,
    enable_dns_hostnames=True,
)

# Create subnets
subnet = aws.ec2.Subnet("plausible-subnet", vpc_id=vpc.id, cidr_block="10.0.1.0/24")

# Create an internet gateway
gateway = aws.ec2.InternetGateway("plausible-igw", vpc_id=vpc.id)

# Create a route table
route_table = aws.ec2.RouteTable(
    "plausible-route-table",
    vpc_id=vpc.id,
    routes=[
        {
            "cidr_block": "0.0.0.0/0",
            "gateway_id": gateway.id,
        }
    ],
)
route_table_association = aws.ec2.RouteTableAssociation(
    "plausible-route-table-association",
    subnet_id=subnet.id,
    route_table_id=route_table.id,
)

# Create a security group
security_group = aws.ec2.SecurityGroup(
    "plausible-sg",
    vpc_id=vpc.id,
    description="Allow web traffic to Plausible",
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 80,
            "to_port": 80,
            "cidr_blocks": ["0.0.0.0/0"],
        },
        {
            "protocol": "tcp",
            "from_port": 443,
            "to_port": 443,
            "cidr_blocks": ["0.0.0.0/0"],
        },
    ],
    egress=[
        {
            "protocol": "-1",
            "from_port": 0,
            "to_port": 0,
            "cidr_blocks": ["0.0.0.0/0"],
        }
    ],
)

# Create the RDS PostgreSQL database
rds_db = aws.rds.Instance(
    "plausible-db",
    engine="postgres",
    instance_class="db.t3.micro",
    allocated_storage=20,
    db_subnet_group_name=aws.rds.SubnetGroup(
        "plausible-db-subnet-group",
        subnet_ids=[subnet.id],
        name="plausible-db-subnet-group",
    ).name,
    vpc_security_group_ids=[security_group.id],
    username="admin",
    password="password",
    skip_final_snapshot=True,
)

# Create an ECS cluster
cluster = aws.ecs.Cluster("plausible-cluster")

# Create a load balancer
alb = aws.lb.LoadBalancer(
    "plausible-lb", security_groups=[security_group.id], subnets=[subnet.id]
)

target_group = aws.lb.TargetGroup(
    "plausible-tg", port=80, protocol="HTTP", vpc_id=vpc.id, target_type="ip"
)

listener = aws.lb.Listener(
    "plausible-listener",
    load_balancer_arn=alb.arn,
    port=80,
    default_actions=[
        {
            "type": "forward",
            "target_group_arn": target_group.arn,
        }
    ],
)

# Create ECS Task Definition
task_definition = aws.ecs.TaskDefinition(
    "plausible-task",
    family="plausible",
    cpu="256",
    memory="512",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    execution_role_arn=aws.iam.Role(
        "ecsTaskExecutionRole",
        assume_role_policy="""{
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "ecs-tasks.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }""",
    ).arn,
    container_definitions=pulumi.Output.all(  # type: ignore[attr-defined]
        rds_db.endpoint
    ).apply(
        lambda db_endpoint: f"""[{
        "name": "plausible",
        "image": "plausible/analytics",
        "cpu": 256,
        "memory": 512,
        "essential": true,
        "portMappings": [
            {
                "containerPort": 8000,
                "hostPort": 8000
            }
        ],
        "environment": [
            {{"name": "DATABASE_URL", "value": "postgres://admin:password@{db_endpoint}:5432/plausible"}}
        ]
    }]"""
    ),
)

# Create ECS service
ecs_service = aws.ecs.Service(
    "plausible-service",
    cluster=cluster.arn,
    task_definition=task_definition.arn,
    desired_count=1,
    launch_type="FARGATE",
    network_configuration={
        "subnets": [subnet.id],
        "security_groups": [security_group.id],
    },
    load_balancers=[
        {
            "target_group_arn": target_group.arn,
            "container_name": "plausible",
            "container_port": 8000,
        }
    ],
)

# Export the load balancer DNS name
pulumi.export("alb_dns", alb.dns_name)  # type: ignore[attr-defined]
