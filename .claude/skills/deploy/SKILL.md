---
name: deploy
description: >
  Deploy complete hackathon infrastructure from scratch including WorkAdventure,
  LiveKit, Coturn, and Jitsi. Use when setting up for a new event, recovering
  from accidental destruction, or first-time deployment. Covers pre-flight checks,
  Terraform bootstrap, map sync, and service verification.
---

# Deploy Hackathon Infrastructure

Deploy the complete nf-core hackathon stack with validation at each step.

**Reference files:**
- [prerequisites.md](prerequisites.md) - First-time setup, secrets, SSH keys
- [oauth-setup.md](oauth-setup.md) - GitHub OAuth configuration
- [service-reference.md](service-reference.md) - Per-service technical details

---

## Pre-flight Checklist

Run all checks before deploying. Stop and fix any failures.

### 1. Environment Variables
```bash
./scripts/validate-env.sh
```
If fails: Run `direnv allow`, check 1Password Environment is mounted.

### 2. AWS Credentials
```bash
aws sts get-caller-identity --profile nf-core
```
If fails: Configure `~/.aws/credentials` with nf-core profile.

### 3. EIP Quota (need 3 available)
```bash
aws ec2 describe-addresses --profile nf-core --region eu-west-1 --query 'length(Addresses)'
```
Must be 5 or less. NEVER release `vpc-multi-runner-*` EIPs.

### 4. Route53 Hosted Zone
```bash
aws route53 list-hosted-zones --profile nf-core --query "HostedZones[?Name=='hackathon.nf-co.re.'].Id" --output text
```
Should return zone ID. If missing, create zone and configure Netlify NS delegation (see [prerequisites.md](prerequisites.md)).

### 5. SSH Key
```bash
ssh-add -l | grep -i 1password
```
Should list keys. If empty, configure 1Password SSH agent (see [prerequisites.md](prerequisites.md)).

---

## Deployment Steps

### Step 1: Bootstrap Terraform Backend
```bash
./scripts/bootstrap.sh
```
Creates S3 bucket and DynamoDB table. Safe to re-run.

### Step 2: Initialize Terraform
```bash
cd terraform/environments/hackathon
terraform init
```

**Important:** All terraform commands must be run from `terraform/environments/hackathon/`, not the root directory.

### Step 3: Review Plan
```bash
terraform plan
```

For fresh deployment, expect ~50-60 resources created, 0 destroyed.

**Stop if plan shows unexpected destroys** - particularly anything with `vpc-multi-runner`.

### Step 4: Apply Infrastructure

**Only proceed after reviewing plan and confirming it looks correct.**

```bash
terraform apply
```

Type `yes` when prompted. Takes 3-5 minutes.

### Step 5: Wait for Services (5-15 minutes)

Services need time to initialize:
1. EC2 boot + cloud-init (2-3 min)
2. Docker pulls + container start (3-5 min)
3. TLS certificates from Let's Encrypt (2-5 min)

Monitor:
```bash
./scripts/status.sh
```

Run every 2-3 minutes. Initially unhealthy is normal.

---

## Verification

Once `status.sh` shows all healthy:

### WorkAdventure
```bash
curl -sI https://app.hackathon.nf-co.re | head -5
```
Expect: HTTP 302 (redirect to OAuth) or HTTP 200

### LiveKit
```bash
curl -s https://livekit.hackathon.nf-co.re
```
Expect: `OK`

### Jitsi
```bash
curl -sI https://jitsi.hackathon.nf-co.re | head -5
```
Expect: HTTP 200

### Coturn
Test at https://webrtc.github.io/samples/src/content/peerconnection/trickle-ice/
- Add server: `turn:turn.hackathon.nf-co.re:3478`
- Look for "relay" candidates

For credential generation, see [service-reference.md](service-reference.md#testing-turn).

### Full Stack Test
1. Open https://app.hackathon.nf-co.re
2. Authenticate with GitHub (requires public nf-core membership)
3. Enter virtual world
4. Test proximity video (walk near another user)
5. Test Jitsi (enter a meeting room zone)

---

## Troubleshooting

### Services not healthy after 15 minutes
SSH in and check logs:
```bash
./scripts/ssh.sh wa    # or lk, turn, jitsi
cloud-init status
docker ps
docker compose logs -f
```

### OAuth shows template errors
OAuth templates are copied from the cloned hackathon-infra repo during deployment.
If templates are missing, redeploy the WorkAdventure instance:
```bash
terraform apply -replace="module.workadventure.aws_instance.workadventure"
```

### Let's Encrypt certificate errors
EIP wasn't assigned before cert request. For Jitsi:
```bash
./scripts/ssh.sh jitsi
sudo /usr/share/jitsi-meet/scripts/install-letsencrypt-cert.sh
```

For Coturn/LiveKit, restart Caddy:
```bash
docker restart caddy
```

### Terraform state lock
1. Wait 15 minutes (locks auto-expire)
2. Check no other terraform process running
3. **NEVER force-unlock** without explicit user approval

### user_data changes not detected
The EC2 instances use `lifecycle { ignore_changes = [ami, user_data] }` to prevent cascading destroys. If you need to apply user_data changes, there are two approaches:

#### Choosing between Terraform and SSH

| Scenario | Preferred Approach |
|----------|-------------------|
| **Development** (no event, single dev) | Terraform force-replace. Downtime acceptable, reproducibility matters. |
| **Live event** (users online, urgent fix) | SSH if possible. Minimize disruption. Terraform only if SSH cannot achieve the fix cleanly. |

**Default to Terraform** unless the user indicates there's an active event with users online.

**Always ask the user before proceeding if downtime is involved:**
> "This change requires redeploying the WorkAdventure instance, which will cause ~2-3 minutes of downtime. Is that acceptable, or would you prefer I attempt an SSH fix?"

#### Option A: Force replace via Terraform (preferred for development)
```bash
terraform apply -replace="module.workadventure.aws_instance.workadventure"
```
- Causes 2-3 minutes downtime
- Clean, reproducible state
- Changes persisted in git

#### Option B: SSH manual update (only during live events)
SSH to the instance and modify the running configuration directly.
- No downtime (or minimal during service restart)
- Changes NOT persisted - will be lost on next Terraform apply
- Higher risk of configuration drift
- Only use for urgent fixes during active events

---

## SSH Notes

The `./scripts/ssh.sh` script opens an interactive SSH session but **does not accept commands as arguments**. To execute commands:

```bash
# Get the IP first
./scripts/ssh.sh wa  # Note the IP shown

# Then run commands directly
ssh ec2-user@<IP> "your command here"
```

Or SSH interactively and run commands manually.
