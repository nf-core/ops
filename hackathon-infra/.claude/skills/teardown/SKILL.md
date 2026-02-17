---
name: teardown
description: >
  Safely tear down hackathon infrastructure. Use when the event is over, doing
  cleanup, or need to start fresh. Covers Terraform destroy (preferred) and
  manual AWS cleanup (when state is corrupted). Includes verification steps
  to ensure complete removal.
---

# Teardown Hackathon Infrastructure

Safely destroy all hackathon infrastructure.

**Reference:** [manual-cleanup-scripts.md](manual-cleanup-scripts.md) - Full scripts for manual AWS cleanup

---

## Pre-Teardown Checklist

### 1. Confirm Intent

**This permanently destroys all infrastructure.** Verify:
- User intends to tear down the entire stack
- No active users in the virtual world

### 2. Verify Maps Are Committed

The `maps/` folder is the source of truth and tracked in git.

```bash
git status maps/
```

If uncommitted changes exist, commit them or confirm they should be discarded.

### 3. Verify Credentials
```bash
./scripts/validate-env.sh
aws sts get-caller-identity --profile nf-core
```

---

## Method 1: Terraform Destroy (Preferred)

Use when Terraform state is healthy and matches AWS.

### Step 1: Check State Health
```bash
cd terraform/environments/hackathon
terraform state list | head -20
```
Should list resources. If errors or empty, use Method 2.

**Important:** All terraform commands must be run from `terraform/environments/hackathon/`.

### Step 2: Disable Prevent Destroy (If Needed)
```bash
grep -r "prevent_destroy" terraform/
```
If found, temporarily set to `false`. Re-enable after teardown.

### Step 3: Review Destruction Plan
```bash
terraform plan -destroy
```

Verify:
- All hackathon resources listed (~50-60 resources)
- No `vpc-multi-runner` resources (CI infrastructure - DO NOT TOUCH)
- DNS records but NOT the hosted zone

### Step 4: Execute Destruction

**Only with explicit user confirmation:**
```bash
terraform destroy
```

Type `yes` when prompted. Takes 5-10 minutes.

### Step 5: Verify
```bash
terraform state list
# Should be empty

aws ec2 describe-instances --profile nf-core --region eu-west-1 \
  --filters "Name=tag:Name,Values=nfcore-hackathon-*" \
  --query 'Reservations[].Instances[].[InstanceId,State.Name]' --output table
# Should show no running instances
```

### Step 6: Re-enable Prevent Destroy
If disabled in Step 2, re-enable for safety.

---

## Method 2: Manual AWS Cleanup

Use when:
- Terraform state is corrupted
- `terraform destroy` fails with errors
- Resources exist in AWS but not in state

**See [manual-cleanup-scripts.md](manual-cleanup-scripts.md) for complete step-by-step scripts.**

### Critical: Deletion Order

AWS resources have dependencies. Delete in this exact order:

1. EC2 Instances (wait for termination)
2. IAM Instance Profiles and Roles
3. Elastic IPs
4. Security Groups
5. Subnets
6. Internet Gateway (detach first, then delete)
7. VPC
8. Route53 A Records (NOT the hosted zone!)
9. DynamoDB Lock Table

**WARNING:** Do NOT release `vpc-multi-runner-*` EIPs - those are CI infrastructure.

---

## Post-Teardown Verification

Run all commands - should return empty:

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

```

---

## What to PRESERVE (Never Delete)

| Resource | Reason |
|----------|--------|
| Route53 Hosted Zone | Contains NS records that Netlify points to |
| Netlify DNS Config | External to AWS, manages nf-co.re domain |
| 1Password Secrets | Reusable for next deployment |
| `vpc-multi-runner-*` EIPs | CI runner infrastructure |
| `runs-on--*` instances | CI runner infrastructure |

---

## Troubleshooting

### "Resource has dependencies" errors
Delete in correct order (see above). Dependencies must be removed first.

### Terraform state lock during destroy
1. Wait 15 minutes for auto-expiry
2. Check no other Terraform processes running
3. **Only with explicit user approval:** `terraform force-unlock <lock-id>`

### Resources exist but not in Terraform state
Use Method 2 (Manual Cleanup) for those specific resources, or import them first:
```bash
terraform import <resource_address> <resource_id>
terraform destroy
```
