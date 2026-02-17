---
name: debug
description: >
  Diagnose and fix issues with running hackathon infrastructure. Use when services
  are unhealthy, users report problems, OAuth fails, video doesn't work, or maps
  don't load. Covers SSH access, Docker logs, TLS certificates, and network
  connectivity troubleshooting.
---

# Debug Hackathon Infrastructure

Diagnose and fix issues with the running stack.

**Reference:** [common-issues.md](references/common-issues.md) - Quick lookup table for common problems

---

## Quick Health Check

Start here for any issue:

```bash
hackathon-infra/scripts/status.sh
```

**Don't panic if unhealthy immediately after deploy** - services take 5-15 minutes to initialize.

---

## SSH Access

```bash
hackathon-infra/scripts/ssh.sh wa     # WorkAdventure
hackathon-infra/scripts/ssh.sh lk     # LiveKit
hackathon-infra/scripts/ssh.sh turn   # Coturn
hackathon-infra/scripts/ssh.sh jitsi  # Jitsi
```

**If SSH fails:**

- Check `ssh-add -l` shows keys from 1Password
- Verify instance is running in AWS Console
- Check security group allows port 22

---

## Important

All terraform commands must be run from `terraform/environments/hackathon/`.

---

## General Debugging

Once SSH'd in:

### Check Initialization Status

```bash
cloud-init status
# Success: status: done
# Problem: status: running (still initializing) or status: error
```

### View Startup Logs

```bash
cat /var/log/cloud-init-output.log
# Look for errors near the end
```

### Check Docker Containers

```bash
docker ps
# All containers should show "Up X minutes"
```

### View Container Logs

```bash
docker compose logs -f          # All containers
docker compose logs <service>   # Specific service
```

### Check Resources

```bash
df -h    # Disk space (problem if >90%)
free -h  # Memory (problem if very low)
```

---

## Service-Specific Issues

### WorkAdventure

**OAuth shows template errors:**
OAuth templates are copied from the cloned hackathon-infra repo during deployment.
If templates are missing, redeploy the WorkAdventure instance:

```bash
cd hackathon-infra/terraform/environments/hackathon
terraform apply -replace="module.workadventure.aws_instance.workadventure"
```

**Containers keep restarting:**

```bash
hackathon-infra/scripts/ssh.sh wa
docker compose logs --tail 100 play
docker compose logs --tail 100 back
```

**Map not loading:**
Maps are served from the cloned hackathon-infra repo on the EC2 instance.

```bash
hackathon-infra/scripts/ssh.sh wa
ls /opt/workadventure/hackathon-infra/maps/default/
# If missing or outdated, sync from git:
cd /opt/workadventure/hackathon-infra && git pull
```

Or use `hackathon-infra/scripts/sync-maps.sh` from your local machine.

### LiveKit

**"OK" not returned:**

```bash
hackathon-infra/scripts/ssh.sh lk
curl -s http://localhost:7880  # Check local
docker logs caddy              # Check TLS
```

**TLS certificate errors:**

```bash
docker restart caddy
```

### Coturn

**No relay candidates in Trickle ICE test:**

Most common cause - certificate permissions:

```bash
hackathon-infra/scripts/ssh.sh turn
ls -la /etc/coturn/certs/
# Must be 644, if not:
sudo chmod 644 /etc/coturn/certs/*
docker restart coturn
```

### Jitsi

**Let's Encrypt failed:**

```bash
hackathon-infra/scripts/ssh.sh jitsi
sudo /usr/share/jitsi-meet/scripts/install-letsencrypt-cert.sh
```

**"service-unavailable" errors:**

```bash
hackathon-infra/scripts/ssh.sh jitsi
docker compose restart prosody
sleep 10
docker compose restart jicofo
docker compose restart jvb
```

---

## Network Debugging

### DNS Not Resolving

```bash
dig +short app.hackathon.nf-co.re
dig +short livekit.hackathon.nf-co.re
dig +short jitsi.hackathon.nf-co.re
dig +short turn.hackathon.nf-co.re
```

### Test Port Connectivity

```bash
nc -zv livekit.hackathon.nf-co.re 443
nc -zv jitsi.hackathon.nf-co.re 443
nc -zuv turn.hackathon.nf-co.re 3478  # UDP
```

### Check Security Groups

```bash
aws ec2 describe-security-groups --profile nf-core --region eu-west-1 \
  --filters "Name=tag:Name,Values=nfcore-hackathon-*" \
  --query 'SecurityGroups[].[GroupName,IpPermissions]' --output json
```

---

## Terraform State Issues

### Recovery from State Corruption

If Terraform state doesn't match AWS reality:

1. **Don't panic** - AWS resources still exist
2. Compare state vs reality (commands below)
3. For resources in AWS but not state: `terraform import <address> <id>`
4. For resources in state but not AWS: `terraform state rm <address>`
5. Run `terraform plan` to verify alignment

**For complete manual cleanup:** See [teardown skill](../hackathon-teardown/SKILL.md) and [manual-cleanup-scripts.md](../hackathon-teardown/references/manual-cleanup-scripts.md)

### State Doesn't Match AWS

```bash
# What Terraform thinks exists
terraform state list

# What actually exists
aws ec2 describe-instances --profile nf-core --region eu-west-1 \
  --filters "Name=tag:Name,Values=nfcore-hackathon-*" \
  --query 'Reservations[].Instances[].[InstanceId,Tags[?Key==`Name`].Value|[0],State.Name]' \
  --output table
```

**Resource in AWS but not state:** `terraform import <address> <id>`
**Resource in state but not AWS:** `terraform state rm <address>`

### State Lock Errors

1. Wait 15 minutes (auto-expire)
2. Check no other terraform process running
3. **NEVER force-unlock** without explicit user approval

---

## Recovery Actions

### Restart Single Service

```bash
hackathon-infra/scripts/ssh.sh <service>
docker compose restart
```

### Full Redeploy

```bash
cd hackathon-infra/terraform/environments/hackathon
terraform destroy
terraform apply
# Wait 10-15 minutes
hackathon-infra/scripts/status.sh
```

Maps and assets are automatically cloned from the hackathon-infra repo during deployment.

---

## Browser-Side Debugging

### Check Console (F12)

- JavaScript errors
- Failed network requests
- CORS errors

### Common Browser Issues

| Issue              | Cause                             | Fix                                        |
| ------------------ | --------------------------------- | ------------------------------------------ |
| WebSocket failed   | Back service not reachable        | Check `docker compose logs back`           |
| Map not loading    | Maps not synced or git not pulled | Run `hackathon-infra/scripts/sync-maps.sh` |
| Audio/video denied | HTTPS or permissions              | Ensure HTTPS, grant permissions            |
