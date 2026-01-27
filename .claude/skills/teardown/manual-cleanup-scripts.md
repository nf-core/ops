# Manual Cleanup Scripts

Complete scripts for manually cleaning up AWS resources when Terraform state is corrupted.

## Important: Deletion Order

AWS resources have dependencies. Delete in this exact order to avoid errors:

1. EC2 Instances (wait for termination)
2. IAM Instance Profiles and Roles
3. Elastic IPs
4. Security Groups
5. Subnets
6. Internet Gateway
7. VPC
8. Route53 A Records
9. DynamoDB Table

---

## Full Cleanup Script

Run these commands in order. Wait for each section to complete before proceeding.

### 1. Terminate EC2 Instances

```bash
# List hackathon instances
aws ec2 describe-instances --profile nf-core --region eu-west-1 \
  --filters "Name=tag:Name,Values=nfcore-hackathon-*" \
           "Name=instance-state-name,Values=running,pending,stopping,stopped" \
  --query 'Reservations[].Instances[].[InstanceId,Tags[?Key==`Name`].Value|[0]]' \
  --output table

# Get instance IDs
INSTANCE_IDS=$(aws ec2 describe-instances --profile nf-core --region eu-west-1 \
  --filters "Name=tag:Name,Values=nfcore-hackathon-*" \
           "Name=instance-state-name,Values=running,pending,stopping,stopped" \
  --query 'Reservations[].Instances[].InstanceId' --output text)

echo "Terminating: $INSTANCE_IDS"

# Terminate instances
if [ -n "$INSTANCE_IDS" ]; then
  aws ec2 terminate-instances --profile nf-core --region eu-west-1 \
    --instance-ids $INSTANCE_IDS

  # Wait for termination
  echo "Waiting for instances to terminate..."
  aws ec2 wait instance-terminated --profile nf-core --region eu-west-1 \
    --instance-ids $INSTANCE_IDS
  echo "Instances terminated."
fi
```

### 2. Delete IAM Instance Profiles and Roles

**This step is commonly missed and causes conflicts on redeployment.**

```bash
# Loop through all hackathon services
for service in livekit coturn jitsi workadventure; do
  PROFILE="nfcore-hackathon-${service}-profile"
  ROLE="nfcore-hackathon-${service}-role"
  
  echo "=== Cleaning up $service ==="
  
  # Remove role from instance profile
  aws iam remove-role-from-instance-profile --profile nf-core \
    --instance-profile-name "$PROFILE" \
    --role-name "$ROLE" 2>/dev/null && echo "Removed role from profile" || echo "Profile/role link not found"
  
  # Delete instance profile
  aws iam delete-instance-profile --profile nf-core \
    --instance-profile-name "$PROFILE" 2>/dev/null && echo "Deleted instance profile" || echo "Instance profile not found"
  
  # Detach managed policies from role
  for policy_arn in $(aws iam list-attached-role-policies --profile nf-core \
    --role-name "$ROLE" --query 'AttachedPolicies[].PolicyArn' --output text 2>/dev/null); do
    aws iam detach-role-policy --profile nf-core \
      --role-name "$ROLE" --policy-arn "$policy_arn"
    echo "Detached policy: $policy_arn"
  done
  
  # Delete inline policies from role
  for policy_name in $(aws iam list-role-policies --profile nf-core \
    --role-name "$ROLE" --query 'PolicyNames[]' --output text 2>/dev/null); do
    aws iam delete-role-policy --profile nf-core \
      --role-name "$ROLE" --policy-name "$policy_name"
    echo "Deleted inline policy: $policy_name"
  done
  
  # Delete role
  aws iam delete-role --profile nf-core \
    --role-name "$ROLE" 2>/dev/null && echo "Deleted role" || echo "Role not found"
  
  echo ""
done
```

### 3. Release Elastic IPs

```bash
# List hackathon EIPs
aws ec2 describe-addresses --profile nf-core --region eu-west-1 \
  --filters "Name=tag:Name,Values=nfcore-hackathon-*" \
  --query 'Addresses[].[AllocationId,PublicIp,Tags[?Key==`Name`].Value|[0]]' \
  --output table

# Release each EIP
for alloc_id in $(aws ec2 describe-addresses --profile nf-core --region eu-west-1 \
  --filters "Name=tag:Name,Values=nfcore-hackathon-*" \
  --query 'Addresses[].AllocationId' --output text); do
  echo "Releasing EIP: $alloc_id"
  aws ec2 release-address --profile nf-core --region eu-west-1 \
    --allocation-id "$alloc_id"
done
```

**WARNING:** Do NOT release EIPs with `vpc-multi-runner` in the name.

### 4. Delete Security Groups

```bash
# List security groups
aws ec2 describe-security-groups --profile nf-core --region eu-west-1 \
  --filters "Name=tag:Name,Values=nfcore-hackathon-*" \
  --query 'SecurityGroups[].[GroupId,GroupName]' --output table

# Delete each security group
for sg_id in $(aws ec2 describe-security-groups --profile nf-core --region eu-west-1 \
  --filters "Name=tag:Name,Values=nfcore-hackathon-*" \
  --query 'SecurityGroups[].GroupId' --output text); do
  echo "Deleting security group: $sg_id"
  aws ec2 delete-security-group --profile nf-core --region eu-west-1 \
    --group-id "$sg_id" 2>/dev/null || echo "Failed - may have dependencies"
done
```

If deletion fails with dependency errors, first delete rules referencing other security groups:
```bash
# Example: Remove all ingress rules from a security group
aws ec2 revoke-security-group-ingress --profile nf-core --region eu-west-1 \
  --group-id <sg-id> --ip-permissions "$(aws ec2 describe-security-groups \
  --profile nf-core --region eu-west-1 --group-ids <sg-id> \
  --query 'SecurityGroups[0].IpPermissions' --output json)"
```

### 5. Delete Subnets

```bash
# List subnets
aws ec2 describe-subnets --profile nf-core --region eu-west-1 \
  --filters "Name=tag:Name,Values=nfcore-hackathon-*" \
  --query 'Subnets[].[SubnetId,CidrBlock,AvailabilityZone]' --output table

# Delete each subnet
for subnet_id in $(aws ec2 describe-subnets --profile nf-core --region eu-west-1 \
  --filters "Name=tag:Name,Values=nfcore-hackathon-*" \
  --query 'Subnets[].SubnetId' --output text); do
  echo "Deleting subnet: $subnet_id"
  aws ec2 delete-subnet --profile nf-core --region eu-west-1 \
    --subnet-id "$subnet_id"
done
```

### 6. Delete Internet Gateway

```bash
# Get IGW and VPC IDs
IGW_ID=$(aws ec2 describe-internet-gateways --profile nf-core --region eu-west-1 \
  --filters "Name=tag:Name,Values=nfcore-hackathon-*" \
  --query 'InternetGateways[0].InternetGatewayId' --output text)

VPC_ID=$(aws ec2 describe-internet-gateways --profile nf-core --region eu-west-1 \
  --filters "Name=tag:Name,Values=nfcore-hackathon-*" \
  --query 'InternetGateways[0].Attachments[0].VpcId' --output text)

echo "IGW: $IGW_ID, VPC: $VPC_ID"

# Detach from VPC
if [ "$IGW_ID" != "None" ] && [ -n "$IGW_ID" ]; then
  aws ec2 detach-internet-gateway --profile nf-core --region eu-west-1 \
    --internet-gateway-id "$IGW_ID" --vpc-id "$VPC_ID"
  echo "Detached IGW from VPC"

  # Delete IGW
  aws ec2 delete-internet-gateway --profile nf-core --region eu-west-1 \
    --internet-gateway-id "$IGW_ID"
  echo "Deleted IGW"
fi
```

### 7. Delete VPC

```bash
# Get VPC ID
VPC_ID=$(aws ec2 describe-vpcs --profile nf-core --region eu-west-1 \
  --filters "Name=tag:Name,Values=nfcore-hackathon-*" \
  --query 'Vpcs[0].VpcId' --output text)

echo "VPC: $VPC_ID"

# Delete VPC
if [ "$VPC_ID" != "None" ] && [ -n "$VPC_ID" ]; then
  aws ec2 delete-vpc --profile nf-core --region eu-west-1 --vpc-id "$VPC_ID"
  echo "Deleted VPC"
fi
```

If VPC deletion fails, there may be remaining dependencies (route tables, network ACLs). Check:
```bash
aws ec2 describe-route-tables --profile nf-core --region eu-west-1 \
  --filters "Name=vpc-id,Values=$VPC_ID" --output table
```

### 8. Delete Route53 A Records

**Preserve the hosted zone - only delete A records.**

```bash
# Get Zone ID (replace with your zone ID)
ZONE_ID="Z093837218PZMCKIMUW2V"

# List A records
aws route53 list-resource-record-sets --profile nf-core \
  --hosted-zone-id "$ZONE_ID" \
  --query "ResourceRecordSets[?Type=='A'].[Name,Type]" --output table

# For alias records (ALB), delete like this:
# aws route53 change-resource-record-sets --profile nf-core \
#   --hosted-zone-id "$ZONE_ID" \
#   --change-batch '{
#     "Changes": [{
#       "Action": "DELETE",
#       "ResourceRecordSet": {
#         "Name": "app.hackathon.nf-co.re",
#         "Type": "A",
#         "AliasTarget": {
#           "HostedZoneId": "<ALB-ZONE-ID>",
#           "DNSName": "<ALB-DNS-NAME>",
#           "EvaluateTargetHealth": false
#         }
#       }
#     }]
#   }'

# For simple A records (EIPs), delete like this:
# aws route53 change-resource-record-sets --profile nf-core \
#   --hosted-zone-id "$ZONE_ID" \
#   --change-batch '{
#     "Changes": [{
#       "Action": "DELETE",
#       "ResourceRecordSet": {
#         "Name": "livekit.hackathon.nf-co.re",
#         "Type": "A",
#         "TTL": 300,
#         "ResourceRecords": [{"Value": "<IP-ADDRESS>"}]
#       }
#     }]
#   }'
```

**Note:** It's often easier to delete Route53 records via the AWS Console.

### 9. Delete DynamoDB Lock Table

```bash
aws dynamodb delete-table --profile nf-core --region eu-west-1 \
  --table-name nfcore-hackathon-terraform-lock
```

### 10. (Optional) Delete Terraform State Bucket

Only if doing a complete reset:

```bash
BUCKET="nfcore-hackathon-terraform-state"

# Same versioning cleanup process
aws s3api list-object-versions --profile nf-core --bucket "$BUCKET" \
  --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}' --output json > /tmp/versions.json

if [ -s /tmp/versions.json ] && [ "$(cat /tmp/versions.json)" != '{"Objects": null}' ]; then
  aws s3api delete-objects --profile nf-core --bucket "$BUCKET" \
    --delete file:///tmp/versions.json
fi

aws s3api list-object-versions --profile nf-core --bucket "$BUCKET" \
  --query '{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}' --output json > /tmp/markers.json

if [ -s /tmp/markers.json ] && [ "$(cat /tmp/markers.json)" != '{"Objects": null}' ]; then
  aws s3api delete-objects --profile nf-core --bucket "$BUCKET" \
    --delete file:///tmp/markers.json
fi

aws s3 rb "s3://$BUCKET" --profile nf-core
```

---

## Verification Checklist

Run all these commands - they should return empty results:

```bash
echo "=== Checking for remaining resources ==="

echo "EC2 Instances:"
aws ec2 describe-instances --profile nf-core --region eu-west-1 \
  --filters "Name=tag:Name,Values=nfcore-hackathon-*" \
           "Name=instance-state-name,Values=running,pending,stopping,stopped" \
  --query 'Reservations[].Instances[].InstanceId' --output text

echo "Elastic IPs:"
aws ec2 describe-addresses --profile nf-core --region eu-west-1 \
  --filters "Name=tag:Name,Values=nfcore-hackathon-*" \
  --query 'Addresses[].PublicIp' --output text

echo "VPCs:"
aws ec2 describe-vpcs --profile nf-core --region eu-west-1 \
  --filters "Name=tag:Name,Values=nfcore-hackathon-*" \
  --query 'Vpcs[].VpcId' --output text

echo "Security Groups:"
aws ec2 describe-security-groups --profile nf-core --region eu-west-1 \
  --filters "Name=tag:Name,Values=nfcore-hackathon-*" \
  --query 'SecurityGroups[].GroupId' --output text

echo "IAM Instance Profiles:"
aws iam list-instance-profiles --profile nf-core \
  --query "InstanceProfiles[?contains(InstanceProfileName, 'nfcore-hackathon')].InstanceProfileName" \
  --output text

echo "IAM Roles:"
aws iam list-roles --profile nf-core \
  --query "Roles[?contains(RoleName, 'nfcore-hackathon')].RoleName" \
  --output text

echo "=== Cleanup complete ==="
```
