#!/bin/bash
set -e

exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

echo "Starting LiveKit installation..."

# Update system
dnf update -y
dnf install -y docker docker-compose-plugin jq

# Start Docker
systemctl start docker
systemctl enable docker

# docker compose v2 is included as a docker plugin via dnf

# Get metadata
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
PUBLIC_IP=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/public-ipv4)

DOMAIN="${domain}"
LIVEKIT_DOMAIN="livekit.$DOMAIN"

# Create app directory
mkdir -p /opt/livekit
cd /opt/livekit

# Create LiveKit config
cat > livekit.yaml << EOF
port: 7880
rtc:
  tcp_port: 7881
  port_range_start: 50000
  port_range_end: 60000
  use_external_ip: true
keys:
  ${livekit_api_key}: ${livekit_api_secret}
logging:
  level: info
EOF

# Create Caddy config for automatic TLS
cat > Caddyfile << EOF
$LIVEKIT_DOMAIN {
    reverse_proxy localhost:7880
}
EOF

# Create docker-compose.yml
cat > docker-compose.yml << EOF
version: "3.9"
services:
  livekit:
    image: livekit/livekit-server:latest
    command: --config /etc/livekit.yaml
    restart: unless-stopped
    network_mode: host
    volumes:
      - ./livekit.yaml:/etc/livekit.yaml:ro

  caddy:
    image: caddy:latest
    restart: unless-stopped
    network_mode: host
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config

volumes:
  caddy_data:
  caddy_config:
EOF

# Start services
docker compose up -d

echo "LiveKit installation complete!"
echo "LiveKit domain: $LIVEKIT_DOMAIN"
