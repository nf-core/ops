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
terraform init
```

### Step 3: Sync Maps to S3

**CRITICAL: Must run BEFORE `terraform apply`.**

WorkAdventure downloads OAuth templates from S3 on first boot. Without this, sign-in page shows "Access Denied" XML.

```bash
./scripts/sync-maps.sh
```

Verify:
```bash
aws s3 ls s3://nfcore-hackathon-maps/default/ --profile nf-core
```

### Step 4: Review Plan
```bash
terraform plan
```

For fresh deployment, expect ~50-60 resources created, 0 destroyed.

**Stop if plan shows unexpected destroys** - particularly anything with `vpc-multi-runner`.

### Step 5: Apply Infrastructure

**Only proceed after reviewing plan and confirming it looks correct.**

```bash
terraform apply
```

Type `yes` when prompted. Takes 3-5 minutes.

### Step 6: Wait for Services (5-15 minutes)

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

### OAuth shows "Access Denied" XML
OAuth templates not synced. Fix:
```bash
./scripts/sync-maps.sh
./scripts/ssh.sh wa
cd /opt/workadventure && docker compose restart
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
