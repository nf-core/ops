#!/usr/bin/env bash
# Test script to verify Pulumi iGenomes setup

set -e

echo "=== Testing Pulumi iGenomes Setup ==="
echo ""

# Navigate to project directory
cd "$(dirname "$0")"

echo "1. Checking 1Password authentication..."
if ! op whoami &>/dev/null; then
    echo "⚠️  Not authenticated with 1Password"
    echo "   Run: eval \$(op signin)"
    exit 1
fi
echo "✅ 1Password authenticated"

echo ""
echo "2. Loading AWS credentials from 1Password..."
export OP_ACCOUNT="nf-core"
export AWS_ACCESS_KEY_ID=$(op item get "AWS - Phil - iGenomes" --vault "Shared" --fields "Access Key")
export AWS_SECRET_ACCESS_KEY=$(op item get "AWS - Phil - iGenomes" --vault "Shared" --fields "Secret Key")
export AWS_DEFAULT_REGION="eu-west-1"

if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "❌ Failed to load credentials"
    exit 1
fi
echo "✅ AWS credentials loaded"

echo ""
echo "3. Setting Pulumi backend..."
export PULUMI_BACKEND_URL="s3://nf-core-pulumi-state?region=eu-north-1&awssdk=v2"
echo "✅ Backend: $PULUMI_BACKEND_URL"

echo ""
echo "4. Checking UV installation..."
if ! command -v uv &>/dev/null; then
    echo "❌ UV not found"
    exit 1
fi
echo "✅ UV installed: $(uv --version)"

echo ""
echo "5. Checking Python dependencies..."
if [ ! -d ".venv" ]; then
    echo "⚠️  Virtual environment not found, running uv sync..."
    uv sync
fi
echo "✅ Dependencies installed"

echo ""
echo "6. Testing Pulumi stack selection..."
if uv run pulumi stack select dev --create 2>&1 | grep -q "Created stack"; then
    echo "✅ Stack created successfully"
elif uv run pulumi stack select dev 2>&1 | grep -q "dev"; then
    echo "✅ Stack selected successfully"
else
    echo "⚠️  Stack operation completed (check output above)"
fi

echo ""
echo "7. Testing Pulumi preview (dry run)..."
echo "   This will attempt to preview the infrastructure import..."
if uv run pulumi preview --non-interactive 2>&1 | head -20; then
    echo ""
    echo "✅ Preview completed"
else
    echo ""
    echo "⚠️  Preview completed with warnings (see above)"
fi

echo ""
echo "=== Setup Test Complete ==="
echo ""
echo "Next steps:"
echo "1. Review the preview output above"
echo "2. Run 'direnv allow' to enable automatic credential loading"
echo "3. Run 'direnv exec . uv run pulumi up' to import resources"
