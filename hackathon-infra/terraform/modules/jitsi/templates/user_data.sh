#!/bin/bash
set -e

exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

echo "=========================================="
echo "Starting Jitsi Meet installation..."
echo "=========================================="

DOMAIN="${domain}"
JITSI_DOMAIN="meet.$DOMAIN"
PUBLIC_IP="${public_ip}"
JITSI_SECRET="${jitsi_secret}"
ADMIN_EMAIL="${admin_email}"

echo "Configuration:"
echo "  Jitsi Domain: $JITSI_DOMAIN"
echo "  Public IP: $PUBLIC_IP"
echo "  Admin Email: $ADMIN_EMAIL"

# Update system
echo "Updating system packages..."
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get upgrade -y

# Set hostname
echo "Setting hostname to $JITSI_DOMAIN..."
hostnamectl set-hostname "$JITSI_DOMAIN"

# Add hostname to /etc/hosts
echo "$PUBLIC_IP $JITSI_DOMAIN" >> /etc/hosts

# Install required packages
echo "Installing prerequisites..."
apt-get install -y apt-transport-https gnupg2 curl software-properties-common dnsutils

# Enable universe repository (required for some dependencies)
add-apt-repository -y universe

# Add Prosody repository (required for Jitsi - Ubuntu 22.04's default is too old)
echo "Adding Prosody repository..."
curl -fsSL https://prosody.im/files/prosody-debian-packages.key | gpg --dearmor -o /usr/share/keyrings/prosody-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/prosody-keyring.gpg] http://packages.prosody.im/debian jammy main" > /etc/apt/sources.list.d/prosody.list
apt-get update

# Install lua5.2 BEFORE jitsi-meet (fixes "Prosody is no longer compatible with Lua 5.1" error)
echo "Installing Lua 5.2 for Prosody compatibility..."
apt-get install -y lua5.2

# Add Jitsi repository
echo "Adding Jitsi repository..."
curl -fsSL https://download.jitsi.org/jitsi-key.gpg.key | gpg --dearmor -o /usr/share/keyrings/jitsi-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/jitsi-keyring.gpg] https://download.jitsi.org stable/" > /etc/apt/sources.list.d/jitsi-stable.list
apt-get update

# Pre-configure Jitsi installer to avoid interactive prompts
echo "Pre-configuring Jitsi installer..."
echo "jitsi-videobridge2 jitsi-videobridge/jvb-hostname string $JITSI_DOMAIN" | debconf-set-selections
echo "jitsi-meet-web-config jitsi-meet/cert-choice select Generate a new self-signed certificate" | debconf-set-selections

# Install Jitsi Meet
echo "Installing Jitsi Meet (this takes several minutes)..."
apt-get install -y jitsi-meet

# Wait for DNS to propagate and verify before attempting Let's Encrypt
# Let's Encrypt WILL fail if DNS doesn't resolve to our IP
echo "Waiting for DNS propagation (up to 5 minutes)..."
for i in {1..30}; do
  RESOLVED_IP=$(dig +short $JITSI_DOMAIN || true)
  if [ "$RESOLVED_IP" = "$PUBLIC_IP" ]; then
    echo "DNS resolved correctly: $JITSI_DOMAIN -> $PUBLIC_IP"
    break
  fi
  echo "Waiting for DNS... (attempt $i/30, got: '$RESOLVED_IP', expected: '$PUBLIC_IP')"
  sleep 10
done

# Verify DNS resolved - fail fast if not
RESOLVED_IP=$(dig +short $JITSI_DOMAIN || true)
if [ "$RESOLVED_IP" != "$PUBLIC_IP" ]; then
  echo "ERROR: DNS did not resolve correctly after 5 minutes"
  echo "Expected: $PUBLIC_IP"
  echo "Got: $RESOLVED_IP"
  echo "Let's Encrypt will fail without correct DNS. Aborting."
  exit 1
fi

# Verify instance public IP matches expected (sanity check)
CURRENT_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 || echo "unknown")
echo "Instance public IP: $CURRENT_IP (expected: $PUBLIC_IP)"

# Get Let's Encrypt certificate (retry up to 3 times with increasing delays)
echo "Obtaining Let's Encrypt certificate..."
CERT_SUCCESS=false
for attempt in 1 2 3; do
    echo "Certificate attempt $attempt of 3..."
    if echo "$ADMIN_EMAIL" | /usr/share/jitsi-meet/scripts/install-letsencrypt-cert.sh; then
        echo "Let's Encrypt certificate obtained successfully!"
        CERT_SUCCESS=true
        break
    else
        if [ $attempt -lt 3 ]; then
            WAIT_TIME=$((attempt * 30))
            echo "Certificate attempt $attempt failed, waiting $WAIT_TIME seconds..."
            sleep $WAIT_TIME
        fi
    fi
done

if [ "$CERT_SUCCESS" = false ]; then
    echo "ERROR: Failed to obtain Let's Encrypt certificate after 3 attempts"
    echo "Check: DNS resolution, port 80 accessibility, rate limits"
    exit 1
fi

# Jitsi is installed with default authentication (anonymous for guests)
# No custom Prosody modifications needed - the default config works with WorkAdventure

# Restart services to ensure everything is running properly
echo "Restarting Jitsi services..."
systemctl restart prosody
sleep 5
systemctl restart jicofo
sleep 5
systemctl restart jitsi-videobridge2

# Wait for services to start
echo "Waiting for services to initialize..."
sleep 15

# Verify services are running
echo ""
echo "=========================================="
echo "Checking Jitsi services..."
echo "=========================================="

check_service() {
    if systemctl is-active --quiet "$1"; then
        echo "  $1: OK"
        return 0
    else
        echo "  $1: FAILED"
        return 1
    fi
}

SERVICES_OK=true
check_service prosody || SERVICES_OK=false
check_service jicofo || SERVICES_OK=false
check_service jitsi-videobridge2 || SERVICES_OK=false
check_service nginx || SERVICES_OK=false

echo ""
if [ "$SERVICES_OK" = true ]; then
    echo "=========================================="
    echo "Jitsi Meet installation COMPLETE!"
    echo "=========================================="
    echo ""
    echo "Jitsi URL: https://$JITSI_DOMAIN"
    echo ""
    echo "WorkAdventure Configuration:"
    echo "  JITSI_URL=$JITSI_DOMAIN"
    echo "  JITSI_PRIVATE_MODE=false"
    echo ""
    echo "=========================================="
else
    echo "=========================================="
    echo "WARNING: Some services failed to start!"
    echo "Check logs: /var/log/jitsi/"
    echo "=========================================="
fi
