#!/bin/bash
set -euo pipefail

# Bootstrap Terraform Backend
# ===========================
# This script creates the S3 bucket and DynamoDB table required for Terraform state,
# then generates backend.tf and initializes Terraform.
#
# Prerequisites:
#   - AWS CLI configured
#   - Environment variables loaded via direnv (see .envrc)
#
# Usage: ./scripts/bootstrap.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TF_DIR="$PROJECT_ROOT/terraform/environments/hackathon"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if TF_VAR_ variables are loaded (via direnv)
if [[ -z "${TF_VAR_AWS_PROFILE:-}" ]]; then
    log_error "Environment not loaded!"
    log_error "Please run: direnv allow"
    exit 1
fi

# Validate required variables
REQUIRED_VARS=(
    TF_VAR_AWS_PROFILE
    TF_VAR_AWS_REGION
    TF_VAR_DOMAIN
    TF_VAR_ROUTE53_ZONE_ID
    TF_VAR_PROJECT_NAME
    TF_VAR_SSH_KEY_NAME
    TF_VAR_ADMIN_EMAIL
    TF_VAR_WORKADVENTURE_SECRET_KEY
    TF_VAR_LIVEKIT_API_KEY
    TF_VAR_LIVEKIT_API_SECRET
    TF_VAR_COTURN_SECRET
    TF_VAR_JITSI_SECRET
)

log_info "Validating environment configuration..."
MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [[ -z "${!var:-}" ]]; then
        MISSING_VARS+=("$var")
    fi
done

if [[ ${#MISSING_VARS[@]} -gt 0 ]]; then
    log_error "Missing required variables:"
    for var in "${MISSING_VARS[@]}"; do
        log_error "  - $var"
    done
    log_error ""
    log_error "Please add these to your 1Password Environment."
    log_error "See .env.example for the full list of required variables."
    exit 1
fi

log_info "All required variables present."

echo ""
log_info "Configuration:"
log_info "  PROJECT_NAME:   $TF_VAR_PROJECT_NAME"
log_info "  AWS_PROFILE:    $TF_VAR_AWS_PROFILE"
log_info "  AWS_REGION:     $TF_VAR_AWS_REGION"

# Generate a random suffix for bucket names (8 chars, lowercase alphanumeric)
# Check if we already have a suffix stored
SUFFIX_FILE="$PROJECT_ROOT/.bucket-suffix"
if [[ -f "$SUFFIX_FILE" ]]; then
    BUCKET_SUFFIX=$(cat "$SUFFIX_FILE")
    log_info "Using existing bucket suffix: $BUCKET_SUFFIX"
else
    BUCKET_SUFFIX=$(openssl rand -hex 4)
    echo "$BUCKET_SUFFIX" > "$SUFFIX_FILE"
    log_info "Generated new bucket suffix: $BUCKET_SUFFIX"
fi

STATE_BUCKET="${TF_VAR_PROJECT_NAME}-terraform-state-${BUCKET_SUFFIX}"
LOCK_TABLE="${TF_VAR_PROJECT_NAME}-terraform-locks"

log_info "  State Bucket: $STATE_BUCKET"
log_info "  Lock Table:   $LOCK_TABLE"

echo ""

# Check if backend.tf already exists and has content
BACKEND_FILE="$TF_DIR/backend.tf"
if [[ -f "$BACKEND_FILE" ]] && grep -q "bucket" "$BACKEND_FILE" 2>/dev/null; then
    log_warn "backend.tf already exists. Checking if resources exist..."
    
    # Check if bucket exists
    if aws s3api head-bucket --bucket "$STATE_BUCKET" --profile "$TF_VAR_AWS_PROFILE" 2>/dev/null; then
        log_info "S3 bucket already exists."
        BUCKET_EXISTS=true
    else
        BUCKET_EXISTS=false
    fi
    
    # Check if DynamoDB table exists
    if aws dynamodb describe-table --table-name "$LOCK_TABLE" --profile "$TF_VAR_AWS_PROFILE" --region "$TF_VAR_AWS_REGION" 2>/dev/null >/dev/null; then
        log_info "DynamoDB table already exists."
        TABLE_EXISTS=true
    else
        TABLE_EXISTS=false
    fi
    
    if [[ "$BUCKET_EXISTS" == "true" && "$TABLE_EXISTS" == "true" ]]; then
        log_info "Backend resources already exist. Running terraform init..."
        cd "$TF_DIR"
        terraform init
        log_info "Bootstrap complete!"
        exit 0
    fi
fi

# Create S3 bucket for Terraform state
log_info "Creating S3 bucket: $STATE_BUCKET"
if aws s3api head-bucket --bucket "$STATE_BUCKET" --profile "$TF_VAR_AWS_PROFILE" 2>/dev/null; then
    log_warn "Bucket already exists, skipping creation."
else
    aws s3api create-bucket \
        --bucket "$STATE_BUCKET" \
        --profile "$TF_VAR_AWS_PROFILE" \
        --region "$TF_VAR_AWS_REGION" \
        --create-bucket-configuration LocationConstraint="$AWS_REGION"
    
    # Enable versioning
    aws s3api put-bucket-versioning \
        --bucket "$STATE_BUCKET" \
        --profile "$TF_VAR_AWS_PROFILE" \
        --versioning-configuration Status=Enabled
    
    # Enable encryption
    aws s3api put-bucket-encryption \
        --bucket "$STATE_BUCKET" \
        --profile "$TF_VAR_AWS_PROFILE" \
        --server-side-encryption-configuration '{
            "Rules": [
                {
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }
            ]
        }'
    
    # Block public access
    aws s3api put-public-access-block \
        --bucket "$STATE_BUCKET" \
        --profile "$TF_VAR_AWS_PROFILE" \
        --public-access-block-configuration '{
            "BlockPublicAcls": true,
            "IgnorePublicAcls": true,
            "BlockPublicPolicy": true,
            "RestrictPublicBuckets": true
        }'
    
    log_info "S3 bucket created and configured."
fi

# Create DynamoDB table for state locking
log_info "Creating DynamoDB table: $LOCK_TABLE"
if aws dynamodb describe-table --table-name "$LOCK_TABLE" --profile "$TF_VAR_AWS_PROFILE" --region "$TF_VAR_AWS_REGION" 2>/dev/null >/dev/null; then
    log_warn "DynamoDB table already exists, skipping creation."
else
    aws dynamodb create-table \
        --table-name "$LOCK_TABLE" \
        --profile "$TF_VAR_AWS_PROFILE" \
        --region "$TF_VAR_AWS_REGION" \
        --attribute-definitions AttributeName=LockID,AttributeType=S \
        --key-schema AttributeName=LockID,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --tags Key=Project,Value="$TF_VAR_PROJECT_NAME" Key=ManagedBy,Value=bootstrap
    
    # Wait for table to be active
    log_info "Waiting for DynamoDB table to be active..."
    aws dynamodb wait table-exists \
        --table-name "$LOCK_TABLE" \
        --profile "$TF_VAR_AWS_PROFILE" \
        --region "$TF_VAR_AWS_REGION"
    
    log_info "DynamoDB table created."
fi

# Generate backend.tf
log_info "Generating backend.tf..."
cat > "$BACKEND_FILE" << EOF
# Terraform Backend Configuration
# Generated by scripts/bootstrap.sh - DO NOT EDIT MANUALLY
# To regenerate, delete this file and run ./scripts/bootstrap.sh

terraform {
  backend "s3" {
    bucket         = "$STATE_BUCKET"
    key            = "hackathon/terraform.tfstate"
    region         = "$TF_VAR_AWS_REGION"
    profile        = "$TF_VAR_AWS_PROFILE"
    dynamodb_table = "$LOCK_TABLE"
    encrypt        = true
  }
}
EOF

log_info "backend.tf generated."

# Initialize Terraform
log_info "Initializing Terraform..."
cd "$TF_DIR"
terraform init

echo ""
log_info "=========================================="
log_info "Bootstrap complete!"
log_info "=========================================="
log_info ""
log_info "Backend resources created:"
log_info "  S3 Bucket:      $STATE_BUCKET"
log_info "  DynamoDB Table: $LOCK_TABLE"
log_info ""
log_info "Next steps:"
log_info "  1. Review the generated backend.tf"
log_info "  2. Run: terraform plan"
log_info "  3. Run: terraform apply"
