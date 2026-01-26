#!/bin/bash
set -euo pipefail

# Check infrastructure status
# Usage: ./scripts/status.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TF_DIR="$PROJECT_ROOT/terraform/environments/hackathon"

# Environment variables should be loaded via direnv (see .envrc)
# Required: TF_VAR_AWS_PROFILE, TF_VAR_AWS_REGION, TF_VAR_DOMAIN

echo "=========================================="
echo "Hackathon Infrastructure Status"
echo "=========================================="

# Check if terraform is initialized
if [[ ! -d "$TF_DIR/.terraform" ]]; then
    echo "ERROR: Terraform not initialized. Run 'terraform init' first."
    exit 1
fi

cd "$TF_DIR"

# Get outputs (suppress errors for missing outputs)
DOMAIN=$(terraform output -raw route53_zone_name 2>/dev/null || echo "${TF_VAR_DOMAIN:-example.com}")
WA_URL="https://app.${DOMAIN}"
LK_URL=$(terraform output -raw livekit_url 2>/dev/null || echo "N/A")
TURN_URL=$(terraform output -raw coturn_turn_url 2>/dev/null || echo "N/A")
TURNS_URL=$(terraform output -raw coturn_turns_url 2>/dev/null || echo "N/A")
JITSI_URL="https://meet.${DOMAIN}"

# Get instance IPs from ALB DNS or direct outputs
WA_ALB=$(terraform output -raw workadventure_alb_dns 2>/dev/null || echo "N/A")
LK_IP=$(terraform output -raw livekit_eip_public_ip 2>/dev/null || echo "N/A")
TURN_IP=$(terraform output -raw coturn_public_ip 2>/dev/null || echo "N/A")
JITSI_IP=$(terraform output -raw jitsi_public_ip 2>/dev/null || echo "N/A")

# WorkAdventure is behind ALB, get instance IP via AWS CLI
WA_INSTANCE_ID=$(terraform output -raw workadventure_instance_id 2>/dev/null || echo "")
if [[ -n "$WA_INSTANCE_ID" ]]; then
    WA_IP=$(aws ec2 describe-instances --instance-ids "$WA_INSTANCE_ID" --profile "${TF_VAR_AWS_PROFILE:-nf-core}" --region "${TF_VAR_AWS_REGION:-eu-west-1}" --query 'Reservations[0].Instances[0].PublicIpAddress' --output text 2>/dev/null || echo "N/A")
else
    WA_IP="N/A"
fi

S3_BUCKET=$(terraform output -raw workadventure_s3_bucket 2>/dev/null || echo "N/A")

echo ""
echo "Service URLs:"
echo "  WorkAdventure: $WA_URL"
echo "  LiveKit:       $LK_URL"
echo "  Jitsi:         $JITSI_URL"
echo "  TURN:          $TURN_URL"
echo "  TURNS:         $TURNS_URL"
echo ""
echo "S3 Maps Bucket:  $S3_BUCKET"
echo ""
echo "Instance IPs (for SSH via 1Password agent):"
echo "  WorkAdventure: ssh ec2-user@$WA_IP"
echo "  LiveKit:       ssh ec2-user@$LK_IP"
echo "  Coturn:        ssh ec2-user@$TURN_IP"
echo "  Jitsi:         ssh ubuntu@$JITSI_IP"
echo ""

echo "Health Checks:"
echo "--------------"
echo "(Services take 5-10 minutes to start after terraform apply)"
echo ""

# Check WorkAdventure - verify it returns HTML with WorkAdventure content
# Note: With oauth2-proxy enabled, we expect a redirect (302) to GitHub for unauthenticated requests
if [[ "$WA_URL" != "N/A" ]]; then
    WA_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$WA_URL" 2>/dev/null || echo "failed")
    WA_BODY=$(curl -s "$WA_URL" 2>/dev/null | head -c 1000 || echo "")
    if [[ "$WA_STATUS" == "302" ]] || [[ "$WA_STATUS" == "303" ]]; then
        # Redirect means oauth2-proxy is working - check where it redirects to
        REDIRECT_LOCATION=$(curl -s -I "$WA_URL" 2>/dev/null | grep -i "^location:" | head -1 || echo "")
        if echo "$REDIRECT_LOCATION" | grep -qi "github.com"; then
            echo "  WorkAdventure: OK (oauth2-proxy active, redirects to GitHub)"
        else
            echo "  WorkAdventure: OK (HTTP $WA_STATUS redirect)"
        fi
    elif [[ "$WA_STATUS" == "200" ]] && echo "$WA_BODY" | grep -qi "workadventure\|play.workadventure"; then
        echo "  WorkAdventure: OK (HTTP $WA_STATUS, content verified, no auth)"
    elif [[ "$WA_STATUS" == "200" ]]; then
        echo "  WorkAdventure: PARTIAL (HTTP $WA_STATUS, but content not verified)"
    elif [[ "$WA_STATUS" == "502" ]] || [[ "$WA_STATUS" == "503" ]]; then
        echo "  WorkAdventure: STARTING (HTTP $WA_STATUS - containers still booting)"
    elif [[ "$WA_STATUS" == "403" ]]; then
        echo "  WorkAdventure: AUTH DENIED (HTTP 403 - check GitHub org membership)"
    else
        echo "  WorkAdventure: FAILED (HTTP $WA_STATUS)"
    fi
else
    echo "  WorkAdventure: NOT DEPLOYED"
fi

# Check oauth2-proxy directly (if we can SSH to the instance)
if [[ "$WA_IP" != "N/A" ]] && [[ "$WA_IP" != "None" ]]; then
    # Try to check oauth2-proxy container status via SSH (non-blocking, quick timeout)
    OAUTH2_PROXY_STATUS=$(ssh -o ConnectTimeout=3 -o StrictHostKeyChecking=no -o BatchMode=yes "ec2-user@$WA_IP" "docker ps --filter 'name=oauth2-proxy' --format '{{.Status}}' 2>/dev/null" 2>/dev/null || echo "")
    if [[ -n "$OAUTH2_PROXY_STATUS" ]] && [[ "$OAUTH2_PROXY_STATUS" == *"Up"* ]]; then
        echo "  oauth2-proxy:  OK (container running)"
    elif [[ -n "$OAUTH2_PROXY_STATUS" ]]; then
        echo "  oauth2-proxy:  ISSUE (status: $OAUTH2_PROXY_STATUS)"
    else
        echo "  oauth2-proxy:  UNKNOWN (could not check - SSH may not be configured)"
    fi
fi

# Check LiveKit
if [[ "$LK_URL" != "N/A" ]]; then
    LK_RESPONSE=$(curl -s "$LK_URL" 2>/dev/null || echo "failed")
    if [[ "$LK_RESPONSE" == "OK" ]]; then
        echo "  LiveKit:       OK"
    elif [[ "$LK_RESPONSE" == "failed" ]] || [[ -z "$LK_RESPONSE" ]]; then
        echo "  LiveKit:       STARTING (not responding yet)"
    else
        echo "  LiveKit:       FAILED (response: $LK_RESPONSE)"
    fi
else
    echo "  LiveKit:       NOT DEPLOYED"
fi

# Check TURN port 3478
if [[ "$TURN_IP" != "N/A" ]]; then
    if nc -z -w5 "$TURN_IP" 3478 2>/dev/null; then
        echo "  TURN (3478):   OK"
    else
        echo "  TURN (3478):   FAILED (port not responding)"
    fi
else
    echo "  TURN (3478):   NOT DEPLOYED"
fi

# Check TURNS port 5349
if [[ "$TURN_IP" != "N/A" ]]; then
    if nc -z -w5 "$TURN_IP" 5349 2>/dev/null; then
        echo "  TURNS (5349):  OK"
    else
        echo "  TURNS (5349):  FAILED (port not responding)"
    fi
else
    echo "  TURNS (5349):  NOT DEPLOYED"
fi

# Check Jitsi - verify it returns Jitsi content
if [[ "$JITSI_IP" != "N/A" ]]; then
    JITSI_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$JITSI_URL" 2>/dev/null || echo "failed")
    JITSI_BODY=$(curl -s "$JITSI_URL" 2>/dev/null | head -c 1000 || echo "")
    if [[ "$JITSI_STATUS" == "200" ]] && echo "$JITSI_BODY" | grep -qi "jitsi"; then
        echo "  Jitsi:         OK (HTTP $JITSI_STATUS, content verified)"
    elif [[ "$JITSI_STATUS" == "200" ]]; then
        echo "  Jitsi:         PARTIAL (HTTP $JITSI_STATUS, but content not verified)"
    elif [[ "$JITSI_STATUS" == "000" ]] || [[ "$JITSI_STATUS" == "failed" ]]; then
        echo "  Jitsi:         STARTING (not responding yet - takes ~10 min)"
    else
        echo "  Jitsi:         FAILED (HTTP $JITSI_STATUS)"
    fi
else
    echo "  Jitsi:         NOT DEPLOYED"
fi

# Check S3 maps access
if [[ "$S3_BUCKET" != "N/A" ]]; then
    S3_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://${S3_BUCKET}.s3.${TF_VAR_AWS_REGION:-eu-west-1}.amazonaws.com/maps/default/map.json" 2>/dev/null || echo "failed")
    if [[ "$S3_STATUS" == "200" ]]; then
        echo "  S3 Maps:       OK (HTTP $S3_STATUS)"
    elif [[ "$S3_STATUS" == "403" ]] || [[ "$S3_STATUS" == "404" ]]; then
        echo "  S3 Maps:       NOT SYNCED (run ./scripts/sync-maps.sh)"
    else
        echo "  S3 Maps:       FAILED (HTTP $S3_STATUS)"
    fi
else
    echo "  S3 Maps:       NOT DEPLOYED"
fi

echo ""
echo "TLS Certificates:"
echo "-----------------"

# Check WorkAdventure TLS (via ALB)
if [[ "$WA_URL" != "N/A" ]]; then
    WA_HOST=$(echo "$WA_URL" | sed 's|https://||' | sed 's|/.*||')
    CERT_EXPIRY=$(echo | openssl s_client -servername "$WA_HOST" -connect "${WA_HOST}:443" 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2 || echo "FAILED")
    echo "  WorkAdventure: $CERT_EXPIRY"
fi

# Check LiveKit TLS
if [[ "$LK_URL" != "N/A" ]]; then
    LK_HOST=$(echo "$LK_URL" | sed 's|https://||' | sed 's|/.*||')
    CERT_EXPIRY=$(echo | openssl s_client -servername "$LK_HOST" -connect "${LK_HOST}:443" 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2 || echo "FAILED")
    echo "  LiveKit:       $CERT_EXPIRY"
fi

# Check Coturn TLS (port 5349)
if [[ "$TURN_IP" != "N/A" ]]; then
    TURN_HOST="turn.${DOMAIN}"
    CERT_EXPIRY=$(echo | openssl s_client -servername "$TURN_HOST" -connect "${TURN_HOST}:5349" 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2 || echo "FAILED")
    echo "  Coturn:        $CERT_EXPIRY"
fi

# Check Jitsi TLS
if [[ "$JITSI_IP" != "N/A" ]]; then
    JITSI_HOST="meet.${DOMAIN}"
    CERT_EXPIRY=$(echo | openssl s_client -servername "$JITSI_HOST" -connect "${JITSI_HOST}:443" 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2 || echo "FAILED")
    echo "  Jitsi:         $CERT_EXPIRY"
fi

echo ""
echo "=========================================="
