#!/bin/bash
set -euo pipefail

# =============================================================================
# Pre-flight validation for Hackathon Infrastructure
# =============================================================================
# This script validates all prerequisites before running terraform apply.
# Run this BEFORE deploying to catch configuration errors early.
#
# Usage: ./scripts/validate-env.sh [--all | --auth | --core]
#   --all   Validate everything (default)
#   --auth  Validate only auth-related variables (Milestone 8)
#   --core  Validate only core infrastructure variables
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# Parse arguments
VALIDATE_MODE="${1:---all}"

echo "=========================================="
echo "Pre-flight Validation"
echo "=========================================="
echo ""

# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

check_var() {
    local var_name="$1"
    local description="$2"
    local required="${3:-true}"
    
    if [[ -z "${!var_name:-}" ]]; then
        if [[ "$required" == "true" ]]; then
            echo -e "${RED}FAIL${NC} $var_name - $description"
            ((ERRORS++))
        else
            echo -e "${YELLOW}WARN${NC} $var_name - $description (optional, not set)"
            ((WARNINGS++))
        fi
        return 1
    else
        # Mask sensitive values
        if [[ "$var_name" == *"SECRET"* ]] || [[ "$var_name" == *"PASSWORD"* ]] || [[ "$var_name" == *"KEY"* && "$var_name" != *"KEY_NAME"* ]]; then
            echo -e "${GREEN}OK${NC}   $var_name - $description (value: ***masked***)"
        else
            echo -e "${GREEN}OK${NC}   $var_name - $description (value: ${!var_name})"
        fi
        return 0
    fi
}

check_var_format() {
    local var_name="$1"
    local pattern="$2"
    local description="$3"
    
    if [[ -z "${!var_name:-}" ]]; then
        return 1  # Already reported by check_var
    fi
    
    if [[ ! "${!var_name}" =~ $pattern ]]; then
        echo -e "${RED}FAIL${NC} $var_name format invalid - $description"
        ((ERRORS++))
        return 1
    fi
    return 0
}

check_command() {
    local cmd="$1"
    local description="$2"
    
    if command -v "$cmd" &> /dev/null; then
        local version=$($cmd --version 2>&1 | head -n1 || echo "unknown")
        echo -e "${GREEN}OK${NC}   $cmd - $description ($version)"
        return 0
    else
        echo -e "${RED}FAIL${NC} $cmd - $description (not found in PATH)"
        ((ERRORS++))
        return 1
    fi
}

# -----------------------------------------------------------------------------
# Check environment is loaded (via direnv)
# -----------------------------------------------------------------------------

echo "Checking environment..."
if [[ -z "${TF_VAR_AWS_PROFILE:-}" ]]; then
    echo -e "${RED}FAIL${NC} Environment not loaded"
    echo ""
    echo "To fix: Run 'direnv allow' in the project root"
    exit 1
fi
echo -e "${GREEN}OK${NC}   Environment loaded via direnv"
echo ""

# -----------------------------------------------------------------------------
# Check required tools
# -----------------------------------------------------------------------------

echo "Checking required tools..."
echo "--------------------------"
check_command "terraform" "Infrastructure as Code"
check_command "aws" "AWS CLI"
check_command "curl" "HTTP client"
check_command "openssl" "TLS/crypto tools"
check_command "jq" "JSON processor" || true  # Optional but useful
echo ""

# -----------------------------------------------------------------------------
# Core Infrastructure Variables
# -----------------------------------------------------------------------------

if [[ "$VALIDATE_MODE" == "--all" ]] || [[ "$VALIDATE_MODE" == "--core" ]]; then
    echo "Checking core infrastructure variables..."
    echo "-----------------------------------------"
    
    check_var "TF_VAR_AWS_PROFILE" "AWS CLI profile name"
    check_var "TF_VAR_AWS_REGION" "AWS region for deployment"
    check_var "TF_VAR_DOMAIN" "Base domain (e.g., hackathon.nf-co.re)"
    check_var "TF_VAR_ROUTE53_ZONE_ID" "Route53 hosted zone ID"
    check_var "TF_VAR_PROJECT_NAME" "Resource naming prefix"
    check_var "TF_VAR_SSH_KEY_NAME" "SSH key pair name in AWS"
    check_var "TF_VAR_ADMIN_EMAIL" "Email for Let's Encrypt certificates"
    
    # Secrets
    check_var "TF_VAR_WORKADVENTURE_SECRET_KEY" "WorkAdventure session secret"
    check_var "TF_VAR_LIVEKIT_API_KEY" "LiveKit API key"
    check_var "TF_VAR_LIVEKIT_API_SECRET" "LiveKit API secret"
    check_var "TF_VAR_COTURN_SECRET" "Coturn TURN server secret"
    check_var "TF_VAR_JITSI_SECRET" "Jitsi authentication secret"
    
    echo ""
    
    # Validate formats
    echo "Validating variable formats..."
    echo "------------------------------"
    
    # AWS Region format
    if [[ -n "${TF_VAR_AWS_REGION:-}" ]]; then
        if [[ "$TF_VAR_AWS_REGION" =~ ^[a-z]{2}-[a-z]+-[0-9]+$ ]]; then
            echo -e "${GREEN}OK${NC}   TF_VAR_AWS_REGION format valid"
        else
            echo -e "${RED}FAIL${NC} TF_VAR_AWS_REGION format invalid (expected: eu-west-1, us-east-1, etc.)"
            ((ERRORS++))
        fi
    fi
    
    # Domain format (should not start with https://)
    if [[ -n "${TF_VAR_DOMAIN:-}" ]]; then
        if [[ "$TF_VAR_DOMAIN" =~ ^https?:// ]]; then
            echo -e "${RED}FAIL${NC} TF_VAR_DOMAIN should not include protocol (remove https://)"
            ((ERRORS++))
        elif [[ "$TF_VAR_DOMAIN" =~ ^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*$ ]]; then
            echo -e "${GREEN}OK${NC}   TF_VAR_DOMAIN format valid"
        else
            echo -e "${YELLOW}WARN${NC} TF_VAR_DOMAIN format may be invalid: $TF_VAR_DOMAIN"
            ((WARNINGS++))
        fi
    fi
    
    # Route53 Zone ID format (starts with Z)
    if [[ -n "${TF_VAR_ROUTE53_ZONE_ID:-}" ]]; then
        if [[ "$TF_VAR_ROUTE53_ZONE_ID" =~ ^Z[A-Z0-9]+$ ]]; then
            echo -e "${GREEN}OK${NC}   TF_VAR_ROUTE53_ZONE_ID format valid"
        else
            echo -e "${RED}FAIL${NC} TF_VAR_ROUTE53_ZONE_ID format invalid (should start with Z)"
            ((ERRORS++))
        fi
    fi
    
    # Secret lengths (should be sufficiently long)
    for secret_var in TF_VAR_WORKADVENTURE_SECRET_KEY TF_VAR_LIVEKIT_API_SECRET TF_VAR_COTURN_SECRET TF_VAR_JITSI_SECRET; do
        if [[ -n "${!secret_var:-}" ]]; then
            len=${#!secret_var}
            if [[ $len -lt 32 ]]; then
                echo -e "${YELLOW}WARN${NC} $secret_var is short ($len chars) - recommend 64+ chars"
                ((WARNINGS++))
            else
                echo -e "${GREEN}OK${NC}   $secret_var length adequate ($len chars)"
            fi
        fi
    done
    
    echo ""
fi

# -----------------------------------------------------------------------------
# GitHub OAuth Variables (Milestone 8)
# -----------------------------------------------------------------------------

if [[ "$VALIDATE_MODE" == "--all" ]] || [[ "$VALIDATE_MODE" == "--auth" ]]; then
    echo "Checking GitHub OAuth variables (Milestone 8)..."
    echo "-------------------------------------------------"
    
    check_var "TF_VAR_GITHUB_OAUTH_CLIENT_ID" "GitHub OAuth App Client ID"
    check_var "TF_VAR_GITHUB_OAUTH_CLIENT_SECRET" "GitHub OAuth App Client Secret"
    check_var "TF_VAR_OAUTH2_PROXY_COOKIE_SECRET" "oauth2-proxy cookie encryption secret"
    
    echo ""
    
    # Validate OAuth formats
    echo "Validating OAuth variable formats..."
    echo "------------------------------------"
    
    # GitHub Client ID format (typically 20 chars, alphanumeric)
    if [[ -n "${TF_VAR_GITHUB_OAUTH_CLIENT_ID:-}" ]]; then
        if [[ "$TF_VAR_GITHUB_OAUTH_CLIENT_ID" =~ ^[a-zA-Z0-9_-]+$ ]] && [[ ${#TF_VAR_GITHUB_OAUTH_CLIENT_ID} -ge 10 ]]; then
            echo -e "${GREEN}OK${NC}   TF_VAR_GITHUB_OAUTH_CLIENT_ID format valid"
        else
            echo -e "${YELLOW}WARN${NC} TF_VAR_GITHUB_OAUTH_CLIENT_ID format unusual (expected alphanumeric, 20 chars)"
            ((WARNINGS++))
        fi
    fi
    
    # GitHub Client Secret format (typically 40 chars)
    if [[ -n "${TF_VAR_GITHUB_OAUTH_CLIENT_SECRET:-}" ]]; then
        if [[ ${#TF_VAR_GITHUB_OAUTH_CLIENT_SECRET} -ge 30 ]]; then
            echo -e "${GREEN}OK${NC}   TF_VAR_GITHUB_OAUTH_CLIENT_SECRET length valid"
        else
            echo -e "${RED}FAIL${NC} TF_VAR_GITHUB_OAUTH_CLIENT_SECRET too short (expected 40+ chars)"
            ((ERRORS++))
        fi
    fi
    
    # Cookie secret should be base64 encoded, ~44 chars for 32 bytes
    if [[ -n "${TF_VAR_OAUTH2_PROXY_COOKIE_SECRET:-}" ]]; then
        if [[ ${#TF_VAR_OAUTH2_PROXY_COOKIE_SECRET} -ge 32 ]]; then
            echo -e "${GREEN}OK${NC}   TF_VAR_OAUTH2_PROXY_COOKIE_SECRET length valid"
        else
            echo -e "${RED}FAIL${NC} TF_VAR_OAUTH2_PROXY_COOKIE_SECRET too short (run: openssl rand -base64 32)"
            ((ERRORS++))
        fi
    fi
    
    echo ""
fi

# -----------------------------------------------------------------------------
# AWS Connectivity Check
# -----------------------------------------------------------------------------

if [[ "$VALIDATE_MODE" == "--all" ]] || [[ "$VALIDATE_MODE" == "--core" ]]; then
    echo "Checking AWS connectivity..."
    echo "----------------------------"
    
    if [[ -n "${TF_VAR_AWS_PROFILE:-}" ]]; then
        # Check AWS credentials
        if aws sts get-caller-identity --profile "$TF_VAR_AWS_PROFILE" &> /dev/null; then
            ACCOUNT_ID=$(aws sts get-caller-identity --profile "$TF_VAR_AWS_PROFILE" --query 'Account' --output text 2>/dev/null)
            echo -e "${GREEN}OK${NC}   AWS credentials valid (Account: $ACCOUNT_ID)"
        else
            echo -e "${RED}FAIL${NC} AWS credentials invalid or expired for profile: $TF_VAR_AWS_PROFILE"
            ((ERRORS++))
        fi
        
        # Check Route53 zone exists
        if [[ -n "${TF_VAR_ROUTE53_ZONE_ID:-}" ]]; then
            if aws route53 get-hosted-zone --id "$TF_VAR_ROUTE53_ZONE_ID" --profile "$TF_VAR_AWS_PROFILE" &> /dev/null; then
                ZONE_NAME=$(aws route53 get-hosted-zone --id "$TF_VAR_ROUTE53_ZONE_ID" --profile "$TF_VAR_AWS_PROFILE" --query 'HostedZone.Name' --output text 2>/dev/null | sed 's/\.$//')
                echo -e "${GREEN}OK${NC}   Route53 zone exists: $ZONE_NAME"
                
                # Check domain matches zone
                if [[ -n "${TF_VAR_DOMAIN:-}" ]] && [[ "$TF_VAR_DOMAIN" != *"$ZONE_NAME"* ]] && [[ "$ZONE_NAME" != *"$TF_VAR_DOMAIN"* ]]; then
                    echo -e "${YELLOW}WARN${NC} TF_VAR_DOMAIN ($TF_VAR_DOMAIN) may not match Route53 zone ($ZONE_NAME)"
                    ((WARNINGS++))
                fi
            else
                echo -e "${RED}FAIL${NC} Route53 zone not found: $TF_VAR_ROUTE53_ZONE_ID"
                ((ERRORS++))
            fi
        fi
        
        # Check SSH key exists
        if [[ -n "${TF_VAR_SSH_KEY_NAME:-}" ]]; then
            if aws ec2 describe-key-pairs --key-names "$TF_VAR_SSH_KEY_NAME" --profile "$TF_VAR_AWS_PROFILE" --region "${TF_VAR_AWS_REGION:-eu-west-1}" &> /dev/null; then
                echo -e "${GREEN}OK${NC}   SSH key pair exists: $TF_VAR_SSH_KEY_NAME"
            else
                echo -e "${RED}FAIL${NC} SSH key pair not found in AWS: $TF_VAR_SSH_KEY_NAME"
                echo "       Create it in AWS Console or import your public key"
                ((ERRORS++))
            fi
        fi
        
        # Check EIP quota (need 3 for LiveKit, Coturn, Jitsi)
        EIP_COUNT=$(aws ec2 describe-addresses --profile "$TF_VAR_AWS_PROFILE" --region "${TF_VAR_AWS_REGION:-eu-west-1}" --query 'length(Addresses)' --output text 2>/dev/null || echo "0")
        EIP_LIMIT=8  # Default AWS limit
        EIP_AVAILABLE=$((EIP_LIMIT - EIP_COUNT))
        if [[ $EIP_AVAILABLE -ge 3 ]]; then
            echo -e "${GREEN}OK${NC}   EIP quota sufficient ($EIP_COUNT used, ~$EIP_AVAILABLE available)"
        else
            echo -e "${YELLOW}WARN${NC} EIP quota may be insufficient ($EIP_COUNT used, need 3 for deployment)"
            ((WARNINGS++))
        fi
    fi
    
    echo ""
fi

# -----------------------------------------------------------------------------
# Terraform State Check
# -----------------------------------------------------------------------------

if [[ "$VALIDATE_MODE" == "--all" ]] || [[ "$VALIDATE_MODE" == "--core" ]]; then
    echo "Checking Terraform configuration..."
    echo "-----------------------------------"
    
    TF_DIR="$PROJECT_ROOT/terraform/environments/hackathon"
    
    # Check backend.tf exists
    if [[ -f "$TF_DIR/backend.tf" ]]; then
        echo -e "${GREEN}OK${NC}   backend.tf exists"
    else
        echo -e "${YELLOW}WARN${NC} backend.tf not found - run ./scripts/bootstrap.sh first"
        ((WARNINGS++))
    fi
    
    # Check if terraform is initialized
    if [[ -d "$TF_DIR/.terraform" ]]; then
        echo -e "${GREEN}OK${NC}   Terraform initialized"
    else
        echo -e "${YELLOW}WARN${NC} Terraform not initialized - run 'terraform init' in $TF_DIR"
        ((WARNINGS++))
    fi
    
    echo ""
fi

# -----------------------------------------------------------------------------
# GitHub OAuth App Validation (if possible)
# -----------------------------------------------------------------------------

if [[ "$VALIDATE_MODE" == "--all" ]] || [[ "$VALIDATE_MODE" == "--auth" ]]; then
    echo "Validating GitHub OAuth App configuration..."
    echo "--------------------------------------------"
    
    if [[ -n "${TF_VAR_GITHUB_OAUTH_CLIENT_ID:-}" ]] && [[ -n "${TF_VAR_DOMAIN:-}" ]]; then
        # We can't validate the OAuth app directly without making an auth request,
        # but we can remind about the callback URL
        EXPECTED_CALLBACK="https://app.${TF_VAR_DOMAIN}/oauth2/callback"
        echo -e "${GREEN}INFO${NC} Expected callback URL: $EXPECTED_CALLBACK"
        echo "      Verify this matches your GitHub OAuth App settings"
        echo ""
        echo "      GitHub OAuth App settings:"
        echo "      https://github.com/organizations/nf-core/settings/applications"
    fi
    
    echo ""
fi

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------

echo "=========================================="
echo "Validation Summary"
echo "=========================================="

if [[ $ERRORS -eq 0 ]] && [[ $WARNINGS -eq 0 ]]; then
    echo -e "${GREEN}All checks passed!${NC}"
    echo ""
    echo "You can proceed with deployment:"
    echo "  cd terraform/environments/hackathon"
    echo "  terraform plan"
    echo "  terraform apply"
    exit 0
elif [[ $ERRORS -eq 0 ]]; then
    echo -e "${YELLOW}Passed with $WARNINGS warning(s)${NC}"
    echo ""
    echo "Review warnings above, but you may proceed with deployment."
    exit 0
else
    echo -e "${RED}Failed with $ERRORS error(s) and $WARNINGS warning(s)${NC}"
    echo ""
    echo "Fix the errors above before running terraform apply."
    exit 1
fi
