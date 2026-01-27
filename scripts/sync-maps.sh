#!/bin/bash
# Sync maps to WorkAdventure server
#
# Maps are served directly from the cloned hackathon-infra repo on the EC2 instance.
# This script SSHs into the server and pulls the latest changes.
#
# For development: Make changes locally, commit, push, then run this script.
# For deployment: Maps are automatically pulled during EC2 initialization.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the WorkAdventure server IP
echo -e "${YELLOW}Getting WorkAdventure server IP...${NC}"
cd "$(dirname "$0")/../terraform/environments/hackathon"

WA_IP=$(terraform output -raw workadventure_instance_id 2>/dev/null | xargs -I {} aws ec2 describe-instances --instance-ids {} --query 'Reservations[0].Instances[0].PublicIpAddress' --output text --profile nf-core --region eu-west-1 2>/dev/null)

if [ -z "$WA_IP" ] || [ "$WA_IP" == "None" ]; then
    echo -e "${RED}Error: Could not get WorkAdventure server IP${NC}"
    echo "Make sure the infrastructure is deployed and you have AWS credentials configured."
    exit 1
fi

echo -e "${GREEN}WorkAdventure server IP: $WA_IP${NC}"

# SSH into the server and update maps
echo -e "${YELLOW}Updating maps on server...${NC}"
ssh -o StrictHostKeyChecking=accept-new ec2-user@$WA_IP << 'ENDSSH'
set -e
cd /opt/workadventure/hackathon-infra

echo "Pulling latest changes..."
git pull

# Ensure the script symlink exists (dist/ contains pre-built scripts)
[ -L maps/default/script ] || ln -s dist maps/default/script

echo "Maps updated successfully!"
ENDSSH

echo -e "${GREEN}Done! Maps synced to server.${NC}"
echo -e "${YELLOW}Note: Users may need to refresh their browser to see changes.${NC}"
