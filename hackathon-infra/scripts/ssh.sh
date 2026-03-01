#!/bin/bash
set -euo pipefail

# SSH to instances using 1Password SSH agent
# Usage: ./scripts/ssh.sh <workadventure|livekit|coturn|jitsi>
# Aliases: wa, lk, turn, jitsi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TF_DIR="$PROJECT_ROOT/terraform/environments/hackathon"

# Environment variables should be loaded via direnv (see .envrc)
# Required: TF_VAR_AWS_PROFILE, TF_VAR_AWS_REGION

TARGET=${1:-}

# Check if terraform is initialized
if [[ ! -d "$TF_DIR/.terraform" ]]; then
    echo "ERROR: Terraform not initialized. Run 'terraform init' first."
    exit 1
fi

cd "$TF_DIR"

case $TARGET in
    workadventure|wa)
        # WorkAdventure is behind ALB, get instance IP via AWS CLI
        WA_INSTANCE_ID=$(terraform output -raw workadventure_instance_id 2>/dev/null)
        IP=$(aws ec2 describe-instances --instance-ids "$WA_INSTANCE_ID" --profile "${TF_VAR_AWS_PROFILE:-nf-core}" --region "${TF_VAR_AWS_REGION:-eu-west-1}" --query 'Reservations[0].Instances[0].PublicIpAddress' --output text 2>/dev/null)
        NAME="WorkAdventure"
        USER="ec2-user"
        ;;
    livekit|lk)
        IP=$(terraform output -raw livekit_eip_public_ip 2>/dev/null)
        NAME="LiveKit"
        USER="ec2-user"
        ;;
    coturn|turn)
        IP=$(terraform output -raw coturn_public_ip 2>/dev/null)
        NAME="Coturn"
        USER="ec2-user"
        ;;
    jitsi)
        IP=$(terraform output -raw jitsi_public_ip 2>/dev/null)
        NAME="Jitsi"
        USER="ubuntu"
        ;;
    "")
        echo "Usage: $0 <target>"
        echo ""
        echo "Targets:"
        echo "  workadventure, wa  - SSH to WorkAdventure instance"
        echo "  livekit, lk        - SSH to LiveKit instance"
        echo "  coturn, turn       - SSH to Coturn instance"
        echo "  jitsi              - SSH to Jitsi instance"
        echo ""
        echo "Note: SSH key is provided by 1Password SSH agent."
        echo "      Ensure 1Password is unlocked and SSH agent is configured."
        exit 1
        ;;
    *)
        echo "ERROR: Unknown target '$TARGET'"
        echo "Valid targets: workadventure (wa), livekit (lk), coturn (turn), jitsi"
        exit 1
        ;;
esac

if [[ -z "$IP" || "$IP" == "" ]]; then
    echo "ERROR: Could not get IP for $NAME. Is the infrastructure deployed?"
    exit 1
fi

echo "Connecting to $NAME at $IP..."
echo "(Using 1Password SSH agent for authentication)"
echo ""

# SSH using 1Password SSH agent (no key file needed)
ssh -o StrictHostKeyChecking=accept-new "${USER:-ec2-user}@$IP"
