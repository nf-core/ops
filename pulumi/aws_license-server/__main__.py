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


license_server = aws.ec2.SecurityGroup(
    "license-server",
    description="security group for sentieon license server",
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            cidr_blocks=["0.0.0.0/0"],
            description="",
            from_port=4,
            ipv6_cidr_blocks=[],
            prefix_list_ids=[],
            protocol="icmp",
            security_groups=[],
            self=False,
            to_port=-1,
        ),
        aws.ec2.SecurityGroupEgressArgs(
            cidr_blocks=["0.0.0.0/0"],
            description="",
            from_port=11,
            ipv6_cidr_blocks=[],
            prefix_list_ids=[],
            protocol="icmp",
            security_groups=[],
            self=False,
            to_port=-1,
        ),
        aws.ec2.SecurityGroupEgressArgs(
            cidr_blocks=["52.89.132.242/32"],
            description="",
            from_port=443,
            ipv6_cidr_blocks=[],
            prefix_list_ids=[],
            protocol="tcp",
            security_groups=[],
            self=False,
            to_port=443,
        ),
        aws.ec2.SecurityGroupEgressArgs(
            cidr_blocks=[],
            description="",
            from_port=-1,
            ipv6_cidr_blocks=["::/0"],
            prefix_list_ids=[],
            protocol="icmpv6",
            security_groups=[],
            self=False,
            to_port=-1,
        ),
        aws.ec2.SecurityGroupEgressArgs(
            cidr_blocks=["0.0.0.0/0"],
            description="",
            from_port=3,
            ipv6_cidr_blocks=[],
            prefix_list_ids=[],
            protocol="icmp",
            security_groups=[],
            self=False,
            to_port=-1,
        ),
        aws.ec2.SecurityGroupEgressArgs(
            cidr_blocks=["0.0.0.0/0"],
            description="",
            from_port=22,
            ipv6_cidr_blocks=["::/0"],
            prefix_list_ids=[],
            protocol="tcp",
            security_groups=[],
            self=False,
            to_port=22,
        ),
        aws.ec2.SecurityGroupEgressArgs(
            cidr_blocks=["0.0.0.0/0"],
            description="",
            from_port=0,
            ipv6_cidr_blocks=[],
            prefix_list_ids=[],
            protocol="-1",
            security_groups=[],
            self=False,
            to_port=0,
        ),
        aws.ec2.SecurityGroupEgressArgs(
            cidr_blocks=["0.0.0.0/0"],
            description="",
            from_port=8,
            ipv6_cidr_blocks=[],
            prefix_list_ids=[],
            protocol="icmp",
            security_groups=[],
            self=False,
            to_port=-1,
        ),
    ],
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            cidr_blocks=["0.0.0.0/0"],
            description="",
            from_port=-1,
            ipv6_cidr_blocks=[],
            prefix_list_ids=[],
            protocol="icmp",
            security_groups=[],
            self=False,
            to_port=-1,
        ),
        aws.ec2.SecurityGroupIngressArgs(
            cidr_blocks=["0.0.0.0/0"],
            description="",
            from_port=22,
            ipv6_cidr_blocks=[],
            prefix_list_ids=[],
            protocol="tcp",
            security_groups=[],
            self=False,
            to_port=22,
        ),
        aws.ec2.SecurityGroupIngressArgs(
            cidr_blocks=[],
            description="",
            from_port=-1,
            ipv6_cidr_blocks=["::/0"],
            prefix_list_ids=[],
            protocol="icmpv6",
            security_groups=[],
            self=False,
            to_port=-1,
        ),
        aws.ec2.SecurityGroupIngressArgs(
            cidr_blocks=[
                "10.0.0.0/16",
                "0.0.0.0/0",
            ],
            description="",
            from_port=8990,
            ipv6_cidr_blocks=["::/0"],
            prefix_list_ids=[],
            protocol="tcp",
            security_groups=[],
            self=False,
            to_port=8990,
        ),
    ],
    name="sentieon-license-server",
    tags={
        "Name": "sentieon-license-server-security-group",
    },
    vpc_id="vpc-09544162c32f4affc",
    opts=pulumi.ResourceOptions(protect=True),
)


sentieon_license_server = aws.ec2.Instance(
    "sentieon-license-server",
    tags={
        "Name": "Sentieon License Server",
    },
    ami="ami-0551ce4d67096d606",
    associate_public_ip_address=True,
    availability_zone="eu-west-1b",
    capacity_reservation_specification=aws.ec2.InstanceCapacityReservationSpecificationArgs(
        capacity_reservation_preference="open",
    ),
    cpu_options=aws.ec2.InstanceCpuOptionsArgs(
        core_count=1,
        threads_per_core=2,
    ),
    credit_specification=aws.ec2.InstanceCreditSpecificationArgs(
        cpu_credits="unlimited",
    ),
    ebs_optimized=True,
    instance_initiated_shutdown_behavior="stop",
    instance_type=aws.ec2.InstanceType.T3_NANO,
    key_name="Edmund 1Password",
    maintenance_options=aws.ec2.InstanceMaintenanceOptionsArgs(
        auto_recovery="default",
    ),
    metadata_options=aws.ec2.InstanceMetadataOptionsArgs(
        http_put_response_hop_limit=2,
        http_tokens="required",
        instance_metadata_tags="disabled",
    ),
    private_dns_name_options=aws.ec2.InstancePrivateDnsNameOptionsArgs(
        hostname_type="ip-name",
    ),
    private_ip="10.0.30.227",
    root_block_device=aws.ec2.InstanceRootBlockDeviceArgs(
        iops=3000,
        throughput=125,
        volume_size=8,
        volume_type="gp3",
    ),
    subnet_id="subnet-040e9b9afcb44f3f9",
    tenancy=aws.ec2.Tenancy.DEFAULT,
    vpc_security_group_ids=["sg-0050bb55ca1c6292c"],
    opts=pulumi.ResourceOptions(protect=True),
    user_data=licsrvr.name.apply(lambda name: f"""#!/usr/bin/bash -xv
yum update -y
yum install amazon-cloudwatch-agent -y
mkdir -p /opt/aws/amazon-cloudwatch-agent/bin
echo '{{ "agent": {{ "run_as_user": "root" }}, "logs": {{ "logs_collected": {{ "files": {{ "collect_list": [ {{ "file_path": "/opt/sentieon/licsrvr.log", "log_group_name": "{name}", "log_stream_name": "{{instance_id}}", "retention_in_days": 120 }} ] }} }} }} }}' > /opt/aws/amazon-cloudwatch-agent/bin/config.json
amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/opt/aws/amazon-cloudwatch-agent/bin/config.json
mkdir -p /opt/sentieon
cd /opt/sentieon
aws s3 cp 's3://sentieon-release/software/sentieon-genomics-{sentieon_version}.tar.gz' - | tar -zxf -
ln -s 'sentieon-genomics-{sentieon_version}' 'sentieon-genomics'
aws s3 cp "{license_s3_uri}" "./sentieon.lic"
i=0
while true; do
  if getent ahosts "{licsrvr_fqdn}"; then
    break
  fi
  i=$((i + 1))
  if [[ i -gt 300 ]]; then
    exit 1
  fi
  sleep 1
done
sentieon-genomics/bin/sentieon licsrvr --start --log licsrvr.log ./sentieon.lic
"""))
)
