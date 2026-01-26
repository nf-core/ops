#!/bin/bash
set -euo pipefail

# Sync maps to S3 bucket
# Usage: ./scripts/sync-maps.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MAPS_DIR="$PROJECT_ROOT/maps"
ASSETS_DIR="$PROJECT_ROOT/assets"
TERRAFORM_DIR="$PROJECT_ROOT/terraform/environments/hackathon"

# Environment variables should be loaded via direnv (see .envrc)
# Required: TF_VAR_AWS_PROFILE

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check for required tools
if ! command -v aws &> /dev/null; then
  log_error "AWS CLI not found. Please install it first."
  exit 1
fi

if ! command -v terraform &> /dev/null; then
  log_error "Terraform not found. Please install it first."
  exit 1
fi

# Check maps directory exists
if [ ! -d "$MAPS_DIR" ]; then
  log_error "Maps directory not found: $MAPS_DIR"
  exit 1
fi

# Validate maps before syncing
log_info "Validating maps..."
if ! "$SCRIPT_DIR/validate-maps.sh"; then
  log_error "Map validation failed. Please fix errors before syncing."
  exit 1
fi
echo ""

# Build TypeScript scripts if package.json exists in map directories
for map_dir in "$MAPS_DIR"/*/; do
  if [ -f "$map_dir/package.json" ]; then
    map_name=$(basename "$map_dir")
    log_info "Building scripts for map: $map_name"
    cd "$map_dir"
    if [ ! -d "node_modules" ]; then
      log_info "Installing npm dependencies..."
      npm install --silent
    fi
    npm run build --silent
    log_info "Script build complete for $map_name"
  fi
done
echo ""

# Get bucket name from Terraform output
log_info "Getting S3 bucket name from Terraform..."
cd "$TERRAFORM_DIR"

BUCKET_NAME=$(terraform output -raw workadventure_s3_bucket 2>/dev/null || echo "")

if [ -z "$BUCKET_NAME" ]; then
  log_error "Could not get S3 bucket name from Terraform output."
  log_error "Make sure the WorkAdventure module has been applied."
  log_error "Run: cd $TERRAFORM_DIR && terraform output"
  exit 1
fi

log_info "S3 Bucket: $BUCKET_NAME"

# Check if there are any files to sync (including audio files)
FILE_COUNT=$(find "$MAPS_DIR" -type f \( -name "*.json" -o -name "*.png" -o -name "*.jpg" -o -name "*.gif" -o -name "*.mp3" -o -name "*.wav" -o -name "*.ogg" \) | wc -l | tr -d ' ')

if [ "$FILE_COUNT" -eq 0 ]; then
  log_warn "No map files found in $MAPS_DIR"
  log_warn "Create map.json and tileset files before syncing."
  exit 0
fi

log_info "Found $FILE_COUNT map files to sync"
log_info "Syncing maps to s3://$BUCKET_NAME/maps/"

# Sync maps to S3 (excluding source/build files, only syncing map assets and built scripts)
# Use --exclude patterns with wildcards to properly exclude all nested paths
aws s3 sync "$MAPS_DIR" "s3://$BUCKET_NAME/maps/" \
  --exclude "*.md" \
  --exclude ".git*" \
  --exclude ".DS_Store" \
  --exclude "*.tmx" \
  --exclude "*/node_modules/*" \
  --exclude "*/src/*" \
  --exclude "*/dist/*" \
  --exclude "*/package.json" \
  --exclude "*/package-lock.json" \
  --exclude "*/tsconfig.json" \
  --exclude "*/vite.config.ts" \
  --exclude "*/.gitignore" \
  --exclude "*/script.js" \
  --delete \
  --cache-control "public, max-age=3600" \
  --profile "${TF_VAR_AWS_PROFILE:-nf-core}"

# Sync dist contents to script subdirectory for each map that has built scripts
for map_dir in "$MAPS_DIR"/*/; do
  if [ -d "$map_dir/dist" ]; then
    map_name=$(basename "$map_dir")
    log_info "Syncing built scripts for map: $map_name"
    aws s3 sync "$map_dir/dist/" "s3://$BUCKET_NAME/maps/$map_name/script/" \
      --delete \
      --cache-control "public, max-age=3600" \
      --profile "${TF_VAR_AWS_PROFILE:-nf-core}"
  fi
done

log_info "Maps synced successfully!"

# Sync assets to S3 (logos, images, etc.)
if [ -d "$ASSETS_DIR" ]; then
  log_info "Syncing assets to s3://$BUCKET_NAME/assets/"
  aws s3 sync "$ASSETS_DIR" "s3://$BUCKET_NAME/assets/" \
    --exclude ".git*" \
    --exclude ".DS_Store" \
    --exclude "*.md" \
    --delete \
    --cache-control "public, max-age=86400" \
    --profile "${TF_VAR_AWS_PROFILE:-nf-core}"
  log_info "Assets synced successfully!"
fi

# List synced files
echo ""
log_info "Synced files:"
aws s3 ls "s3://$BUCKET_NAME/maps/" --recursive --profile "${AWS_PROFILE:-nf-core}"

# Test public access
echo ""
log_info "Testing public access..."
MAP_URL="https://$BUCKET_NAME.s3.eu-west-1.amazonaws.com/maps/default/map.json"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$MAP_URL" 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
  log_info "Public access OK: $MAP_URL"
else
  log_warn "Public access returned HTTP $HTTP_CODE"
  log_warn "If this is a new map, it may take a moment to be accessible."
fi

echo ""
log_info "Map base URL: https://$BUCKET_NAME.s3.eu-west-1.amazonaws.com/maps/"
