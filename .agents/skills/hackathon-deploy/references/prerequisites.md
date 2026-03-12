# Prerequisites and Environment Setup

First-time setup requirements before deploying hackathon infrastructure.

## Required Tools

```bash
# macOS
brew install awscli terraform direnv
brew install --cask 1password 1password-cli

# Verify versions
aws --version      # v2.x required
terraform version  # v1.5+ required
op --version       # 1Password CLI
```

---

## AWS Configuration

### Profile Setup

Create `~/.aws/credentials`:

```ini
[nf-core]
aws_access_key_id = AKIA...
aws_secret_access_key = ...
region = eu-west-1
```

### Verify Access

```bash
aws sts get-caller-identity --profile nf-core
```

---

## Environment Variables

All variables are managed via 1Password Environments and direnv.

### Required Variables

| Variable          | Example              | Description                       |
| ----------------- | -------------------- | --------------------------------- |
| `AWS_PROFILE`     | `nf-core`            | AWS CLI profile name              |
| `AWS_REGION`      | `eu-west-1`          | AWS region                        |
| `DOMAIN`          | `hackathon.nf-co.re` | Base domain for services          |
| `ROUTE53_ZONE_ID` | `Z093837218...`      | Route53 hosted zone ID            |
| `PROJECT_NAME`    | `nfcore-hackathon`   | Prefix for AWS resources          |
| `SSH_KEY_NAME`    | `nfcore-hackathon`   | SSH key name in 1Password and AWS |
| `ADMIN_EMAIL`     | `admin@nf-co.re`     | Email for Let's Encrypt           |

### Secret Variables

Generate with `openssl rand -hex 32` (or `-hex 16` for cookie secret):

| Variable                   | Length | Description        |
| -------------------------- | ------ | ------------------ |
| `WORKADVENTURE_SECRET_KEY` | 64 hex | Session signing    |
| `LIVEKIT_API_KEY`          | 32 hex | LiveKit API key    |
| `LIVEKIT_API_SECRET`       | 64 hex | LiveKit API secret |
| `COTURN_SECRET`            | 64 hex | TURN shared secret |
| `JITSI_SECRET`             | 64 hex | Jitsi auth secret  |

### OAuth Variables

| Variable                     | Source                 | Description                      |
| ---------------------------- | ---------------------- | -------------------------------- |
| `GITHUB_OAUTH_CLIENT_ID`     | GitHub OAuth App       | Client ID (~20 chars)            |
| `GITHUB_OAUTH_CLIENT_SECRET` | GitHub OAuth App       | Client secret (~40 chars)        |
| `OAUTH2_PROXY_COOKIE_SECRET` | `openssl rand -hex 16` | **Must be exactly 32 hex chars** |

**CRITICAL:** Cookie secret must be exactly 32 hex characters (16 bytes). Do NOT use base64 encoding.

### Generate All Secrets

```bash
echo "=== Copy these to 1Password Environment ==="
echo "WORKADVENTURE_SECRET_KEY=$(openssl rand -hex 32)"
echo "LIVEKIT_API_KEY=$(openssl rand -hex 16)"
echo "LIVEKIT_API_SECRET=$(openssl rand -hex 32)"
echo "COTURN_SECRET=$(openssl rand -hex 32)"
echo "JITSI_SECRET=$(openssl rand -hex 32)"
echo "OAUTH2_PROXY_COOKIE_SECRET=$(openssl rand -hex 16)"
```

---

## SSH Key Setup

### Create SSH Key in 1Password

```bash
op item create \
  --category "SSH Key" \
  --title "nfcore-hackathon" \
  --vault "Dev" \
  --ssh-generate-key ed25519

PUBLIC_KEY=$(op item get "nfcore-hackathon" --vault "Dev" --fields "public key")
```

### Import to AWS

```bash
aws ec2 import-key-pair \
  --key-name nfcore-hackathon \
  --public-key-material fileb://<(echo "$PUBLIC_KEY") \
  --profile nf-core \
  --region eu-west-1
```

### Configure 1Password SSH Agent

1. Open 1Password desktop → **Settings → Developer**
2. Enable **"Use the SSH agent"**
3. Enable **"Integrate with 1Password CLI"**

4. Add to `~/.ssh/config`:

   ```
   Host *
       IdentityAgent "~/Library/Group Containers/2BUA8C4S2C.com.1password/t/agent.sock"
   ```

5. Create `~/.config/1password/ssh/agent.toml`:

   ```toml
   [[ssh-keys]]
   vault = "Dev"
   ```

   **Why this is needed:** By default, 1Password only exposes SSH keys that are individually enabled in the app. This config auto-exposes all keys in the Dev vault.

6. Verify:
   ```bash
   ssh-add -l
   # Should show: 256 SHA256:... nfcore-hackathon (ED25519)
   ```

---

## Route53 Setup

### Check If Zone Exists

```bash
aws route53 list-hosted-zones-by-name --dns-name "hackathon.nf-co.re" --profile nf-core
```

### Create Zone (If Needed)

```bash
aws route53 create-hosted-zone \
  --name "hackathon.nf-co.re" \
  --caller-reference "$(date +%s)" \
  --profile nf-core
```

Note the nameservers from output.

### Configure Netlify NS Delegation

The parent domain `nf-co.re` is managed by Netlify:

1. Go to Netlify DNS settings for `nf-co.re`
2. Add NS records for `hackathon` subdomain pointing to AWS nameservers

### Verify Delegation

```bash
dig NS hackathon.nf-co.re +short
# Should return AWS nameservers
```

---

## 1Password Environment Setup

1. Open **1Password desktop → Developer → Environments**
2. Click **"New Environment"**
3. Add all variables from sections above
4. Click **"Mount"** and select the project root directory
5. The `.env` file should appear (git-ignored)

### Verify Environment

```bash
./scripts/validate-env.sh
```

---

## EIP Quota

The deployment needs 3 Elastic IPs. AWS default limit is 5 per region.

```bash
# Check current usage
aws ec2 describe-addresses --profile nf-core --region eu-west-1 --query 'length(Addresses)'

# List existing EIPs
aws ec2 describe-addresses --profile nf-core --region eu-west-1 \
  --query 'Addresses[].[PublicIp,Tags[?Key==`Name`].Value|[0]]' --output table
```

**Do NOT release:** `vpc-multi-runner-*` EIPs (CI runner infrastructure)

---

## Validation Checklist

Before deploying, verify all items:

- [ ] AWS CLI configured with `nf-core` profile
- [ ] Terraform >= 1.5 installed
- [ ] 1Password SSH agent configured
- [ ] SSH key in both 1Password and AWS
- [ ] Route53 hosted zone exists
- [ ] Netlify NS records point to Route53
- [ ] All secrets generated
- [ ] GitHub OAuth app created (see [oauth-setup.md](oauth-setup.md))
- [ ] 1Password Environment mounted
- [ ] `./scripts/validate-env.sh` passes
- [ ] EIP quota has room for 3 more
