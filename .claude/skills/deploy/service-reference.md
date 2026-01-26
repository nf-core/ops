# Service Reference

Technical details for each service. For architecture rationale, see `docs/architecture.md`.

## WorkAdventure

**Instance:** t3.xlarge | **OS:** Amazon Linux 2023 | **Module:** `terraform/modules/workadventure/`

### Docker Containers
- `play` - Game frontend (ports 3000, 3001 for WebSocket)
- `back` - Backend API
- `map-storage` - Map file management
- `uploader` - File uploads
- `icon` - Avatar icons
- `oauth2-proxy` - GitHub authentication
- `reverse-proxy` - Traefik routing

### Key Configuration
| Variable | Purpose |
|----------|---------|
| `WORKADVENTURE_SECRET_KEY` | Internal API authentication |
| `START_ROOM_URL` | Initial map (S3 URL) |
| `JITSI_URL` | Jitsi server URL |
| `LIVEKIT_URL` | LiveKit server URL |

### Critical Notes
- **PLAY_URL must be `app.${DOMAIN}`** - Traefik routes on `app.` prefix
- **Root volume minimum 30GB** - Amazon Linux 2023 requirement
- **ALB health check uses `200-499` matcher** - Traefik returns 404 for requests without Host header; this is expected
- **Startup time:** 5-10 minutes

---

## LiveKit

**Instance:** c5.xlarge | **OS:** Amazon Linux 2023 | **Module:** `terraform/modules/livekit/`

### Docker Containers
- `livekit` - LiveKit server
- `caddy` - TLS termination

### Ports
| Port | Protocol | Purpose |
|------|----------|---------|
| 443 | TCP | HTTPS API |
| 7880 | TCP | WebRTC signaling |
| 50000-60000 | UDP | WebRTC media |

### Health Check
```bash
curl https://livekit.hackathon.nf-co.re
# Returns: OK
```

### Startup time: 3-5 minutes

---

## Coturn

**Instance:** t3.medium | **OS:** Amazon Linux 2023 | **Module:** `terraform/modules/coturn/`

### Docker Containers
- `coturn` - TURN server
- `caddy` - TLS certificate management

### Ports
| Port | Protocol | Purpose |
|------|----------|---------|
| 3478 | UDP | TURN (unencrypted) |
| 5349 | TCP | TURNS (TLS encrypted) |

### Critical: TLS Certificate Permissions
Coturn runs as non-root. Certificates **must be readable (644)**:
```bash
ls -la /etc/coturn/certs/
# Must show -rw-r--r-- (644)

# If wrong:
sudo chmod 644 /etc/coturn/certs/*
docker restart coturn
```

### Testing TURN
Generate time-limited credentials:
```bash
./scripts/ssh.sh turn
SECRET=$(grep static-auth-secret /etc/coturn/turnserver.conf | cut -d= -f2)
TIMESTAMP=$(($(date +%s) + 3600))
USERNAME="${TIMESTAMP}:testuser"
PASSWORD=$(echo -n "$USERNAME" | openssl dgst -sha1 -hmac "$SECRET" -binary | base64)
echo "Username: $USERNAME"
echo "Password: $PASSWORD"
```

Test at https://webrtc.github.io/samples/src/content/peerconnection/trickle-ice/

### Startup time: 4-5 minutes

---

## Jitsi

**Instance:** t3.medium | **OS:** Ubuntu 22.04 | **Module:** `terraform/modules/jitsi/`

### Why Ubuntu (Not Amazon Linux)?
Jitsi requires specific Prosody packages from the Jitsi apt repository, which only supports Debian/Ubuntu. The user_data script:
1. Adds Prosody upstream repository
2. Installs `lua5.2` (required dependency)
3. Then installs `jitsi-meet`

### Docker Containers
- `prosody` - XMPP server
- `jicofo` - Conference Focus
- `jvb` - Video Bridge
- `web` - Web interface

### Ports
| Port | Protocol | Purpose |
|------|----------|---------|
| 80, 443 | TCP | Web interface |
| 4443 | TCP | JVB fallback |
| 10000 | UDP | JVB media |

### Let's Encrypt Timing
Let's Encrypt may fail on first boot because user_data.sh runs before the EIP is fully associated. The script waits 90 seconds, but sometimes this isn't enough.

If EIP wasn't assigned when cert script ran, re-run:
```bash
./scripts/ssh.sh jitsi
sudo /usr/share/jitsi-meet/scripts/install-letsencrypt-cert.sh
```

### Restart Order (for issues)
```bash
docker compose restart prosody
sleep 10
docker compose restart jicofo
docker compose restart jvb
```

### Startup time: 8-10 minutes

---

## Service Dependencies

```
WorkAdventure ──depends_on──▶ LiveKit
              ──depends_on──▶ Coturn
              ──depends_on──▶ Jitsi
```

**Important:** Changes to LiveKit, Coturn, or Jitsi can trigger WorkAdventure recreation (user_data hash change). Be careful with targeted destroys.
