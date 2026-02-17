#!/bin/bash
set -e
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

echo "Starting WorkAdventure installation..."

dnf update -y
dnf install -y docker docker-compose-plugin git jq

systemctl start docker
systemctl enable docker

mkdir -p /opt/workadventure
cd /opt/workadventure

# Sparse checkout: clone only hackathon-infra/ from nf-core/ops monorepo
git clone --depth 1 --filter=blob:none --sparse https://github.com/nf-core/ops.git ops-repo
cd ops-repo
git sparse-checkout set hackathon-infra
cd /opt/workadventure
# Symlink so all existing paths (/opt/workadventure/hackathon-infra/) keep working
ln -s /opt/workadventure/ops-repo/hackathon-infra /opt/workadventure/hackathon-infra
git clone --depth 1 https://github.com/workadventure/workadventure.git
cd workadventure/contrib/docker

MAP_STORAGE_PASSWORD=$(openssl rand -base64 16 | tr -dc 'a-zA-Z0-9' | head -c 16)
ROOM_API_SECRET=$(openssl rand -hex 32)

cat > .env << EOF
DOMAIN=app.${domain}
VERSION=master
LOG_LEVEL=WARN
HTTP_PORT=80
HTTPS_PORT=443
GRPC_PORT=50051
DATA_DIR=/opt/workadventure/data
RESTART_POLICY=unless-stopped
SECRET_KEY=${workadventure_secret_key}
ROOM_API_SECRET_KEY=$ROOM_API_SECRET
MAP_STORAGE_AUTHENTICATION_USER=admin
MAP_STORAGE_AUTHENTICATION_PASSWORD=$MAP_STORAGE_PASSWORD
PUBLIC_MAP_STORAGE_URL=https://map-storage.${domain}
START_ROOM_URL=/_/global/app.${domain}/maps/default/map.json
SERVER_NAME=nf-core Hackathon
SERVER_MOTD=Welcome to the nf-core hackathon!
SERVER_ICON=https://app.${domain}/assets/logos/nf-core-logo-square.png
CONTACT_URL=https://nf-co.re/join#slack
ENABLE_CHAT=true
ENABLE_CHAT_UPLOAD=false
ENABLE_CHAT_ONLINE_LIST=true
ENABLE_CHAT_DISCONNECTED_LIST=true
ENABLE_MAP_EDITOR=false
MAX_USERNAME_LENGTH=40
ENABLE_REPORT_ISSUES_MENU=false
DISABLE_ANONYMOUS=false
DISABLE_NOTIFICATIONS=false
ACME_EMAIL=${admin_email}
%{ if livekit_url != "" ~}
LIVEKIT_URL=${livekit_url}
LIVEKIT_API_KEY=${livekit_api_key}
LIVEKIT_API_SECRET=${livekit_api_secret}
%{ endif ~}
%{ if jitsi_url != "" ~}
JITSI_URL=${jitsi_url}
JITSI_PRIVATE_MODE=false
%{ else ~}
JITSI_URL=
%{ endif ~}
%{ if turn_server != "" ~}
TURN_SERVER=${turn_server}
TURN_STATIC_AUTH_SECRET=${turn_secret}
%{ endif ~}
KLAXOON_ENABLED=false
YOUTUBE_ENABLED=true
GOOGLE_DRIVE_ENABLED=false
GOOGLE_DOCS_ENABLED=false
GOOGLE_SHEETS_ENABLED=false
GOOGLE_SLIDES_ENABLED=false
ERASER_ENABLED=false
EXCALIDRAW_ENABLED=true
CARDS_ENABLED=false
TLDRAW_ENABLED=false
EOF

mkdir -p /opt/workadventure/data/letsencrypt
mkdir -p /opt/workadventure/oauth2-templates

ASSETS_URL="https://app.${domain}"
sed "s|__S3_BUCKET_URL__|$ASSETS_URL|g" /opt/workadventure/hackathon-infra/assets/templates/sign_in.html > /opt/workadventure/oauth2-templates/sign_in.html
cp /opt/workadventure/hackathon-infra/assets/templates/error.html /opt/workadventure/oauth2-templates/error.html
ln -s dist /opt/workadventure/hackathon-infra/maps/default/script

cat > /opt/workadventure/nginx-maps.conf << 'NGINXCONF'
server {
    listen 80;
    server_name _;
    location /maps/ { alias /usr/share/nginx/html/maps/; add_header Access-Control-Allow-Origin *; }
    location /assets/ { alias /usr/share/nginx/html/assets/; add_header Access-Control-Allow-Origin *; }
    location /static/images/favicons/ {
        alias /usr/share/nginx/html/overrides/static/images/favicons/;
        add_header Access-Control-Allow-Origin *;
    }
}
NGINXCONF

cat > docker-compose.override.yaml << 'OVERRIDE'
version: "3.6"
services:
  reverse-proxy:
    command:
      - --log.level=$${LOG_LEVEL:-WARN}
      - --providers.docker
      - --providers.docker.exposedbydefault=false
      - --entryPoints.web.address=:80
      - --entryPoints.websecure.address=:8443
      - --entryPoints.grpc.address=:50051
  maps:
    image: nginx:alpine
    container_name: maps
    restart: unless-stopped
    volumes:
      - /opt/workadventure/hackathon-infra/maps:/usr/share/nginx/html/maps:ro
      - /opt/workadventure/hackathon-infra/assets:/usr/share/nginx/html/assets:ro
      - /opt/workadventure/hackathon-infra/overrides:/usr/share/nginx/html/overrides:ro
      - /opt/workadventure/nginx-maps.conf:/etc/nginx/conf.d/default.conf:ro
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.maps.rule=Host(\"app.${domain}\") && (PathPrefix(\"/maps\") || PathPrefix(\"/assets/logos\") || PathPrefix(\"/assets/templates\") || PathPrefix(\"/assets/social\"))"
      - "traefik.http.routers.maps.entrypoints=web"
      - "traefik.http.routers.maps.priority=200"
      - "traefik.http.services.maps.loadbalancer.server.port=80"
OVERRIDE

cat >> docker-compose.override.yaml << EOF
  oauth2-proxy:
    image: quay.io/oauth2-proxy/oauth2-proxy:v7.14.2
    container_name: oauth2-proxy
    restart: unless-stopped
    command:
      - --provider=github
      - --github-org=${github_org}
      - --client-id=${github_oauth_client_id}
      - --client-secret=${github_oauth_client_secret}
      - --cookie-secret=${oauth2_proxy_cookie_secret}
      - --cookie-secure=true
      - --cookie-domain=.${domain}
      - --whitelist-domain=.${domain}
      - --email-domain=*
      - --upstream=http://play:3000
      - --http-address=0.0.0.0:4180
      - --reverse-proxy=true
      - --custom-templates-dir=/templates
    volumes:
      - /opt/workadventure/oauth2-templates:/templates:ro
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.oauth2-proxy.rule=Host(\"app.${domain}\") && !PathPrefix(\"/ws\") && !PathPrefix(\"/resources\") && !PathPrefix(\"/static\") && !Path(\"/favicon.ico\") && !PathPrefix(\"/manifest\") && !PathPrefix(\"/icon\") && !PathPrefix(\"/lettericons\") && !PathPrefix(\"/maps\") && !PathPrefix(\"/assets/logos\") && !PathPrefix(\"/assets/templates\") && !PathPrefix(\"/assets/social\")"
      - "traefik.http.routers.oauth2-proxy.entrypoints=web"
      - "traefik.http.services.oauth2-proxy.loadbalancer.server.port=4180"
      - "traefik.http.routers.oauth2-proxy.priority=100"
  play:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.play-ws.rule=Host(\"app.${domain}\") && PathPrefix(\"/ws\")"
      - "traefik.http.routers.play-ws.entrypoints=web"
      - "traefik.http.routers.play-ws.priority=200"
      - "traefik.http.services.play-ws.loadbalancer.server.port=3001"
      - "traefik.http.routers.play-static.rule=Host(\"app.${domain}\") && (PathPrefix(\"/resources\") || PathPrefix(\"/static\") || Path(\"/favicon.ico\") || PathPrefix(\"/manifest\") || PathPrefix(\"/icon\") || PathPrefix(\"/lettericons\") || PathPrefix(\"/assets\"))"
      - "traefik.http.routers.play-static.entrypoints=web"
      - "traefik.http.routers.play-static.priority=150"
      - "traefik.http.services.play-static.loadbalancer.server.port=3000"
EOF

docker-compose -f docker-compose.prod.yaml -f docker-compose.override.yaml up -d
sleep 30
docker exec docker-play-1 ln -sf /usr/src/play/dist/public/resources/objects/webrtc-in-ding.mp3 /usr/src/play/dist/public/resources/objects/webrtc-in.mp3 2>/dev/null || true
docker exec docker-play-1 sed -i 's|{{ title }}|nf-core/hackathon|g' /usr/src/play/dist/public/index.html 2>/dev/null || true

# Copy override assets into play container (favicons, etc.)
if [ -d "/opt/workadventure/hackathon-infra/overrides" ]; then
  echo "Applying asset overrides..."
  docker cp /opt/workadventure/hackathon-infra/overrides/. docker-play-1:/usr/src/play/dist/public/
fi

docker-compose -f docker-compose.prod.yaml -f docker-compose.override.yaml ps
echo "WorkAdventure installation complete! Access: https://app.${domain}"
