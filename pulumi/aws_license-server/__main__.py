import pulumi
import json
import pulumi_aws as aws

# import pulumi_dns as dns
import pulumi_std as std


def not_implemented(msg):
    raise NotImplementedError(msg)


config = pulumi.Config()
aws_region = config.require_object("awsRegion")
licsrvr_fqdn = config.require_object("licsrvrFqdn")
license_s3_uri = config.require_object("licenseS3Uri")
kms_key = config.get_object("kmsKey")
if kms_key is None:
    kms_key = None
sentieon_version = config.get("sentieonVersion")
if sentieon_version is None:
    sentieon_version = "202308.01"
license_bucket_arn = not_implemented(
    'format("arn:aws:s3:::%s",split("/",var.license_s3_uri)[2])'
)
s3_uri_arr = std.split_output(separator="/", text=license_s3_uri).apply(
    lambda invoke: invoke.result
)
license_obj_arn = not_implemented(
    'format("arn:aws:s3:::%s",join("/",slice(local.s3_uri_arr,2,length(local.s3_uri_arr))))'
)
# Find the IP of the master server
# master = dns.index.a_record_set(host="master.sentieon.com")
# Find the default VPC
default = aws.ec2.get_vpc_output(default=True)
# Find the AWS account ID
current = aws.get_caller_identity_output()
## Configure the security group for the license server
# Create a security group
sentieon_license_server = aws.ec2.SecurityGroup(
    "sentieon_license_server",
    name="sentieon_license_server",
    description="Security groups for the Sentieon license server",
    vpc_id=default.id,
)
# Create a security group for the compute nodes
sentieon_compute_nodes = aws.ec2.SecurityGroup(
    "sentieon_compute_nodes",
    name="sentieon_compute",
    description="Security groups for Sentieon compute nodes",
    vpc_id=default.id,
)
# Security group rules are definied in a separate file
# Cloudwatch log group for logs
licsrvr = aws.cloudwatch.LogGroup("licsrvr", name="/sentieon/licsrvr/LicsrvrLog")
# IAM role for the license server
licsrvr_role = aws.iam.Role(
    "licsrvr",
    name="sentieon_licsrvr_role",
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Sid": "",
                    "Principal": {
                        "Service": "ec2.amazonaws.com",
                    },
                }
            ],
        }
    ),
    inline_policies=[
        aws.iam.RoleInlinePolicyArgs(
            name="s3_inline_policy",
            policy=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Action": [
                                "s3:Get*",
                                "s3:List*",
                                "s3-object-lambda:Get*",
                                "s3-object-lambda:List*",
                            ],
                            "Effect": "Allow",
                            "Resource": [
                                license_bucket_arn,
                                license_obj_arn,
                                "arn:aws:s3:::sentieon-release",
                                not_implemented(
                                    'format("arn:aws:s3:::sentieon-release/software/sentieon-genomics-%s.tar.gz",var.sentieon_version)'
                                ),
                            ],
                        }
                    ],
                }
            ),
        ),
        aws.iam.RoleInlinePolicyArgs(
            name="cloudwatch_inline_policy",
            policy=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Action": [
                                "logs:PutRetentionPolicy",
                                "logs:CreateLogGroup",
                                "logs:PutLogEvents",
                                "logs:CreateLogStream",
                            ],
                            "Effect": "Allow",
                            "Resource": [
                                not_implemented(
                                    'format("arn:aws:logs:*:%v:log-group:%v",data.aws_caller_identity.current.account_id,aws_cloudwatch_log_group.licsrvr.name)'
                                ),
                                not_implemented(
                                    'format("arn:aws:logs:*:%v:log-group:%v:log-stream:*",data.aws_caller_identity.current.account_id,aws_cloudwatch_log_group.licsrvr.name)'
                                ),
                            ],
                        }
                    ],
                }
            ),
        ),
    ],
)
licsrvr_instance_profile = aws.iam.InstanceProfile(
    "licsrvr", name="sentieon_licsrvr_profile", role=licsrvr_role.name
)
## Start the License server
# Find the latest Amazon Linux AMI
al2023 = aws.ec2.get_ami_output(
    most_recent=True,
    filters=[
        aws.ec2.GetAmiFilterArgs(
            name="name",
            values=["al2023-ami-2023.*-x86_64"],
        ),
        aws.ec2.GetAmiFilterArgs(
            name="virtualization-type",
            values=["hvm"],
        ),
        aws.ec2.GetAmiFilterArgs(
            name="architecture",
            values=["x86_64"],
        ),
    ],
    owners=["amazon"],
)
# Create the license server instance
sentieon_licsrvr = aws.ec2.Instance(
    "sentieon_licsrvr",
    ami=al2023.id,
    instance_type=aws.ec2.InstanceType.T3_NANO,
    vpc_security_group_ids=[sentieon_license_server.id],
    iam_instance_profile=licsrvr_instance_profile.id,
    user_data_replace_on_change=True,
    root_block_device=aws.ec2.InstanceRootBlockDeviceArgs(
        encrypted=True,
        kms_key_id=kms_key,
    ),
    user_data=licsrvr.name.apply(
        lambda name: f"""#!/usr/bin/bash -xv
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
"""
    ),
)
## Create a private hosted zone
# Create a hosted zone
primary = aws.route53.Zone(
    "primary",
    name=licsrvr_fqdn,
    vpcs=[
        aws.route53.ZoneVpcArgs(
            vpc_id=default.id,
            vpc_region=aws_region,
        )
    ],
)
licsrvr_fqdn_record = aws.route53.Record(
    "licsrvr_fqdn",
    zone_id=primary.zone_id,
    name=licsrvr_fqdn,
    type=aws.route53.RecordType.A,
    ttl=300,
    records=[sentieon_licsrvr.private_ip],
)
## Security groups for the license server
# Ingress - inbound ICMP
inbound_icmp3_master = aws.vpc.SecurityGroupIngressRule(
    "inbound_icmp_3_master",
    security_group_id=sentieon_license_server.id,
    cidr_ipv4=not_implemented(
        'format("%s/32",element(data.dns_a_record_set.master.addrs,0))'
    ),
    ip_protocol="icmp",
    from_port=3,
    to_port=-1,
)
inbound_icmp4_master = aws.vpc.SecurityGroupIngressRule(
    "inbound_icmp_4_master",
    security_group_id=sentieon_license_server.id,
    cidr_ipv4=not_implemented(
        'format("%s/32",element(data.dns_a_record_set.master.addrs,0))'
    ),
    ip_protocol="icmp",
    from_port=4,
    to_port=-1,
)
inbound_icmp3 = aws.vpc.SecurityGroupIngressRule(
    "inbound_icmp_3",
    security_group_id=sentieon_license_server.id,
    cidr_ipv4=default.cidr_block,
    ip_protocol="icmp",
    from_port=3,
    to_port=-1,
)
inbound_icmp4 = aws.vpc.SecurityGroupIngressRule(
    "inbound_icmp_4",
    security_group_id=sentieon_license_server.id,
    cidr_ipv4=default.cidr_block,
    ip_protocol="icmp",
    from_port=4,
    to_port=-1,
)
# Egress - outbound ICMP
outbound_icmp3_master = aws.vpc.SecurityGroupEgressRule(
    "outbound_icmp_3_master",
    security_group_id=sentieon_license_server.id,
    cidr_ipv4=not_implemented(
        'format("%s/32",element(data.dns_a_record_set.master.addrs,0))'
    ),
    ip_protocol="icmp",
    from_port=3,
    to_port=-1,
)
outbound_icmp4_master = aws.vpc.SecurityGroupEgressRule(
    "outbound_icmp_4_master",
    security_group_id=sentieon_license_server.id,
    cidr_ipv4=not_implemented(
        'format("%s/32",element(data.dns_a_record_set.master.addrs,0))'
    ),
    ip_protocol="icmp",
    from_port=4,
    to_port=-1,
)
outbound_icmp3 = aws.vpc.SecurityGroupEgressRule(
    "outbound_icmp_3",
    security_group_id=sentieon_license_server.id,
    cidr_ipv4=default.cidr_block,
    ip_protocol="icmp",
    from_port=3,
    to_port=-1,
)
outbound_icmp4 = aws.vpc.SecurityGroupEgressRule(
    "outbound_icmp_4",
    security_group_id=sentieon_license_server.id,
    cidr_ipv4=default.cidr_block,
    ip_protocol="icmp",
    from_port=4,
    to_port=-1,
)
# Ingress - inbound TCP from the VPC's CIDR
inbound_tcp = aws.vpc.SecurityGroupIngressRule(
    "inbound_tcp",
    security_group_id=sentieon_license_server.id,
    from_port=8990,
    to_port=8990,
    cidr_ipv4=default.cidr_block,
    ip_protocol="tcp",
)
# Egress - https
outbound_https_all = aws.vpc.SecurityGroupEgressRule(
    "outbound_https_all",
    security_group_id=sentieon_license_server.id,
    cidr_ipv4="0.0.0.0/0",
    ip_protocol="tcp",
    from_port=443,
    to_port=443,
)
# Egress - http
outbound_http_all = aws.vpc.SecurityGroupEgressRule(
    "outbound_http_all",
    security_group_id=sentieon_license_server.id,
    cidr_ipv4="0.0.0.0/0",
    ip_protocol="tcp",
    from_port=80,
    to_port=80,
)
## Security groups for the compute nodes
# Ingress - inbound ssh
inbound_ssh_compute = aws.vpc.SecurityGroupIngressRule(
    "inbound_ssh_compute",
    security_group_id=sentieon_compute_nodes.id,
    cidr_ipv4="0.0.0.0/0",
    ip_protocol="tcp",
    from_port=22,
    to_port=22,
)
inbound_ssh_v6_compute = aws.vpc.SecurityGroupIngressRule(
    "inbound_ssh_v6_compute",
    security_group_id=sentieon_compute_nodes.id,
    cidr_ipv6="::/0",
    ip_protocol="tcp",
    from_port=22,
    to_port=22,
)
# Ingress - inbound ICMP
inbound_icmp_compute3 = aws.vpc.SecurityGroupIngressRule(
    "inbound_icmp_compute_3",
    security_group_id=sentieon_compute_nodes.id,
    cidr_ipv4="0.0.0.0/0",
    ip_protocol="icmp",
    from_port=3,
    to_port=-1,
)
inbound_icmp_compute4 = aws.vpc.SecurityGroupIngressRule(
    "inbound_icmp_compute_4",
    security_group_id=sentieon_compute_nodes.id,
    cidr_ipv4="0.0.0.0/0",
    ip_protocol="icmp",
    from_port=4,
    to_port=-1,
)
# Egress - outbound ICMP
outbound_icmp_compute3 = aws.vpc.SecurityGroupEgressRule(
    "outbound_icmp_compute_3",
    security_group_id=sentieon_compute_nodes.id,
    cidr_ipv4="0.0.0.0/0",
    ip_protocol="icmp",
    from_port=3,
    to_port=-1,
)
outbound_icmp_compute4 = aws.vpc.SecurityGroupEgressRule(
    "outbound_icmp_compute_4",
    security_group_id=sentieon_compute_nodes.id,
    cidr_ipv4="0.0.0.0/0",
    ip_protocol="icmp",
    from_port=4,
    to_port=-1,
)
# Egress - ssh
outbound_ssh_compute = aws.vpc.SecurityGroupEgressRule(
    "outbound_ssh_compute",
    security_group_id=sentieon_compute_nodes.id,
    cidr_ipv4="0.0.0.0/0",
    ip_protocol="tcp",
    from_port=22,
    to_port=22,
)
outbound_ssh_v6_compute = aws.vpc.SecurityGroupEgressRule(
    "outbound_ssh_v6_compute",
    security_group_id=sentieon_compute_nodes.id,
    cidr_ipv6="::/0",
    ip_protocol="tcp",
    from_port=22,
    to_port=22,
)
# Egress - outbound TCP to the VPC's CIDR
outbound_tcp_compute = aws.vpc.SecurityGroupEgressRule(
    "outbound_tcp_compute",
    security_group_id=sentieon_compute_nodes.id,
    from_port=8990,
    to_port=8990,
    cidr_ipv4=default.cidr_block,
    ip_protocol="tcp",
)
# Egress - https
outbound_https_all_compute = aws.vpc.SecurityGroupEgressRule(
    "outbound_https_all_compute",
    security_group_id=sentieon_compute_nodes.id,
    cidr_ipv4="0.0.0.0/0",
    ip_protocol="tcp",
    from_port=443,
    to_port=443,
)
# Egress - http
outbound_http_all_compute = aws.vpc.SecurityGroupEgressRule(
    "outbound_http_all_compute",
    security_group_id=sentieon_compute_nodes.id,
    cidr_ipv4="0.0.0.0/0",
    ip_protocol="tcp",
    from_port=80,
    to_port=80,
)
