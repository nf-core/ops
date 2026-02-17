# Common Issues Quick Reference

Quick lookup for common problems. For detailed procedures, see the main SKILL.md.

## Quick Troubleshooting Table

| Issue                          | Likely Cause                      | Solution                                 |
| ------------------------------ | --------------------------------- | ---------------------------------------- |
| Missing .env variables         | 1Password Environment not mounted | `direnv allow`; check 1Password          |
| Terraform state locked         | Another process or stale lock     | Wait 15 min; check DynamoDB              |
| Service not responding         | Startup not complete              | Wait 5-15 min after deploy               |
| OAuth redirect loop            | Cookie issues                     | Clear cookies for `*.hackathon.nf-co.re` |
| Access Denied (403)            | Org membership private            | Make nf-core membership public           |
| "Access Denied" XML on sign-in | OAuth templates issue             | Redeploy WorkAdventure instance          |
| WebSocket errors               | Traefik routing issue             | `docker logs reverse-proxy`              |
| Map not loading                | Git not pulled on server          | `./scripts/sync-maps.sh`                 |
| Let's Encrypt failed           | EIP not ready at boot             | Re-run cert script on instance           |
| No relay candidates (TURN)     | Cert permissions                  | `chmod 644 /etc/coturn/certs/*`          |
| Jitsi "service-unavailable"    | Prosody/Jicofo issue              | Restart services in order                |
| Audio/video not working        | WebRTC connectivity               | Check Coturn is healthy                  |

---

## Service Startup Times

Don't troubleshoot until these times have passed:

| Service       | Startup Time | What's Happening                                         |
| ------------- | ------------ | -------------------------------------------------------- |
| WorkAdventure | 5-10 min     | Docker pull (~10 images), OAuth templates, Traefik certs |
| LiveKit       | 3-5 min      | Docker pull, Caddy TLS cert                              |
| Coturn        | 4-5 min      | Docker pull, Caddy TLS cert, cert copy                   |
| Jitsi         | 8-10 min     | Apt install, Prosody setup, Docker pull, Let's Encrypt   |

---

## Health Check Commands

### All Services

```bash
./scripts/status.sh
```

### Individual Services

```bash
curl -sI https://app.hackathon.nf-co.re | head -5    # WA: 302 or 200
curl -s https://livekit.hackathon.nf-co.re           # LiveKit: "OK"
curl -sI https://jitsi.hackathon.nf-co.re | head -5  # Jitsi: 200
# Coturn: Use Trickle ICE test, look for "relay" candidates
```

### DNS

```bash
dig +short app.hackathon.nf-co.re
dig +short livekit.hackathon.nf-co.re
dig +short jitsi.hackathon.nf-co.re
dig +short turn.hackathon.nf-co.re
```

---

## Video Architecture

| Type            | Provider | When Used                   |
| --------------- | -------- | --------------------------- |
| Proximity video | LiveKit  | Walking near other players  |
| Meeting rooms   | Jitsi    | Entering `jitsiRoom` zone   |
| Silent zones    | N/A      | Areas marked `silent: true` |

---

## Required Ports

| Service       | Inbound Ports                   |
| ------------- | ------------------------------- |
| All           | 22/TCP (SSH)                    |
| WorkAdventure | 80, 443/TCP (via ALB)           |
| LiveKit       | 443, 7880/TCP + 50000-60000/UDP |
| Coturn        | 3478/UDP, 5349/TCP              |
| Jitsi         | 80, 443, 4443/TCP + 10000/UDP   |

---

## Log Locations

| What               | Command                                        |
| ------------------ | ---------------------------------------------- |
| Cloud-init startup | `cat /var/log/cloud-init-output.log`           |
| Cloud-init status  | `cloud-init status`                            |
| Docker containers  | `docker ps`                                    |
| All container logs | `docker compose logs`                          |
| Specific container | `docker compose logs <service>`                |
| Follow logs        | `docker compose logs -f`                       |
| Find errors        | `grep -i error /var/log/cloud-init-output.log` |

---

## General Debug Flow

1. **Check instance running:**

   ```bash
   aws ec2 describe-instances --profile nf-core --region eu-west-1 \
     --filters "Name=tag:Name,Values=nfcore-hackathon-*" \
     --query 'Reservations[].Instances[].[Tags[?Key==`Name`].Value|[0],State.Name]' --output table
   ```

2. **SSH in:**

   ```bash
   ./scripts/ssh.sh <wa|lk|turn|jitsi>
   ```

3. **Check cloud-init:**

   ```bash
   cloud-init status  # Should be "done"
   ```

4. **Check containers:**

   ```bash
   docker ps  # All should show "Up"
   ```

5. **Check logs:**
   ```bash
   docker compose logs <service> | tail -50
   ```

---

## Quick Fixes by Service

### WorkAdventure

| Issue                     | Fix                                              |
| ------------------------- | ------------------------------------------------ |
| OAuth "Access Denied" XML | Redeploy WorkAdventure instance                  |
| ALB 502/503               | Wait 5-10 min, check `docker ps`                 |
| Map not loading           | `./scripts/sync-maps.sh` to pull latest from git |

### LiveKit

| Issue             | Fix                              |
| ----------------- | -------------------------------- |
| "OK" not returned | Check Caddy: `docker logs caddy` |
| TLS errors        | `docker restart caddy`           |

### Coturn

| Issue                | Fix                                                         |
| -------------------- | ----------------------------------------------------------- |
| No relay candidates  | `sudo chmod 644 /etc/coturn/certs/*; docker restart coturn` |
| TLS handshake failed | `docker restart caddy; sleep 30; docker restart coturn`     |

### Jitsi

| Issue                | Fix                                                              |
| -------------------- | ---------------------------------------------------------------- |
| Let's Encrypt failed | `sudo /usr/share/jitsi-meet/scripts/install-letsencrypt-cert.sh` |
| service-unavailable  | Restart in order: prosody → jicofo → jvb                         |
| Video not connecting | Check port 10000/UDP in security group                           |

---

## Emergency Recovery

### Single Service Restart

```bash
./scripts/ssh.sh <service>
docker compose restart
```

### Full Stack Redeploy

```bash
cd terraform/environments/hackathon
terraform destroy
terraform apply
# Wait 10-15 minutes
./scripts/status.sh
```

### State Corruption

See [teardown skill](../teardown/SKILL.md) for manual cleanup procedures.
