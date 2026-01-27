#!/bin/bash
set -euo pipefail

# Validate WorkAdventure maps before syncing to server
# Usage: ./scripts/validate-maps.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MAPS_DIR="$PROJECT_ROOT/maps"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check for required tools
if ! command -v jq &> /dev/null; then
  log_error "jq not found. Please install it (brew install jq / apt install jq)"
  exit 1
fi

if ! command -v python3 &> /dev/null; then
  log_error "python3 not found. Please install it."
  exit 1
fi

# Track validation status
ERRORS=0
WARNINGS=0

# Find all map.json files (excluding dev directories and only matching map.json files)
MAP_FILES=$(find "$MAPS_DIR" -name "map.json" -type f \
  -not -path "*/node_modules/*" \
  -not -path "*/dist/*" \
  -not -path "*/src/*" \
  2>/dev/null || true)

if [ -z "$MAP_FILES" ]; then
  log_error "No JSON map files found in $MAPS_DIR"
  exit 1
fi

log_info "Validating maps in $MAPS_DIR"
echo ""

for MAP_FILE in $MAP_FILES; do
  MAP_DIR=$(dirname "$MAP_FILE")
  MAP_NAME=$(basename "$MAP_DIR")
  
  log_info "Checking: $MAP_NAME/$(basename "$MAP_FILE")"
  
  # 1. Check JSON is valid
  if ! jq empty "$MAP_FILE" 2>/dev/null; then
    log_error "  Invalid JSON syntax"
    ERRORS=$((ERRORS + 1))
    continue
  fi
  log_info "  JSON syntax: OK"
  
  # 2. Check tileset images exist
  MISSING_TILESETS=0
  TILESET_PATHS=$(jq -r '.tilesets[]?.image // empty' "$MAP_FILE" 2>/dev/null || true)
  
  for TILESET in $TILESET_PATHS; do
    # Resolve relative path from map directory
    TILESET_FULL="$MAP_DIR/$TILESET"
    if [ ! -f "$TILESET_FULL" ]; then
      log_error "  Missing tileset: $TILESET"
      MISSING_TILESETS=$((MISSING_TILESETS + 1))
    fi
  done
  
  if [ "$MISSING_TILESETS" -eq 0 ]; then
    TILESET_COUNT=$(echo "$TILESET_PATHS" | grep -c . || echo 0)
    log_info "  Tilesets: OK ($TILESET_COUNT found)"
  else
    ERRORS=$((ERRORS + MISSING_TILESETS))
  fi
  
  # 3. Check for start/spawn layer (layer with startLayer property or named "start")
  HAS_START=$(python3 << EOF
import json
import sys

with open("$MAP_FILE", 'r') as f:
    data = json.load(f)

for layer in data.get('layers', []):
    # Check for startLayer property
    for prop in layer.get('properties', []):
        if prop.get('name') == 'startLayer' and prop.get('value') == True:
            print('yes')
            sys.exit(0)
    
    # Check for layer named "start"
    if layer.get('name', '').lower() == 'start':
        print('yes')
        sys.exit(0)

print('no')
EOF
)
  
  if [ "$HAS_START" = "yes" ]; then
    log_info "  Start layer: OK"
  else
    log_warn "  Start layer: Not found (players may spawn at 0,0)"
    WARNINGS=$((WARNINGS + 1))
  fi
  
  # 4. Check map dimensions
  WIDTH=$(jq -r '.width // 0' "$MAP_FILE")
  HEIGHT=$(jq -r '.height // 0' "$MAP_FILE")
  TILE_WIDTH=$(jq -r '.tilewidth // 0' "$MAP_FILE")
  TILE_HEIGHT=$(jq -r '.tileheight // 0' "$MAP_FILE")
  
  if [ "$TILE_WIDTH" -ne 32 ] || [ "$TILE_HEIGHT" -ne 32 ]; then
    log_warn "  Tile size: ${TILE_WIDTH}x${TILE_HEIGHT} (WorkAdventure expects 32x32)"
    WARNINGS=$((WARNINGS + 1))
  else
    log_info "  Dimensions: ${WIDTH}x${HEIGHT} tiles (${TILE_WIDTH}x${TILE_HEIGHT}px each)"
  fi
  
  echo ""
done

# Summary
echo "================================"
if [ "$ERRORS" -gt 0 ]; then
  log_error "Validation FAILED: $ERRORS error(s), $WARNINGS warning(s)"
  exit 1
elif [ "$WARNINGS" -gt 0 ]; then
  log_warn "Validation passed with $WARNINGS warning(s)"
  exit 0
else
  log_info "Validation PASSED"
  exit 0
fi
