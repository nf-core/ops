---
name: maps
description: >
  Validate and sync WorkAdventure maps to S3. Use when working with map files,
  syncing changes, checking for map errors, or setting up interactive zones
  (Jitsi rooms, silent areas). Covers JSON validation, TypeScript builds, S3 sync,
  and troubleshooting map loading issues.
---

# Maps: Validate and Sync

This skill covers validating and syncing WorkAdventure maps. 

**Important workflow note:** Map editing is done by humans using the Tiled Map Editor. AI agents assist with validation, building TypeScript scripts, and syncing to S3.

For map editing instructions, see `maps/README.md`.

## Map Architecture Overview

```
maps/                          # Local source (tracked in git)
├── default/
│   ├── map.json              # Main map file (edited in Tiled)
│   └── tilesets/             # Tileset images
├── src/                      # TypeScript scripts (optional)
│   └── main.ts
└── dist/                     # Built scripts (generated)

        ↓ sync-maps.sh ↓

S3: nfcore-hackathon-maps/    # Remote (ephemeral, recreated on deploy)
├── default/
│   ├── map.json
│   └── tilesets/
├── script/                   # Built TypeScript
└── assets/                   # OAuth templates, etc.
```

**Critical:** The `maps/` folder in this repository is the **source of truth**. S3 is ephemeral and destroyed with the infrastructure. Always commit map changes to git before teardown.

---

## Pre-Sync Checklist

### 1. Verify Environment

```bash
./scripts/validate-env.sh
```

**Success:** All required variables present.

### 2. Verify AWS Access

```bash
aws s3 ls s3://nfcore-hackathon-maps --profile nf-core 2>/dev/null && echo "Bucket exists" || echo "Bucket does not exist"
```

**If bucket doesn't exist:** The infrastructure hasn't been deployed yet, or was torn down. Run `terraform apply` first (see deploy skill), or sync will create a local-only build.

---

## Sync Maps to S3

```bash
./scripts/sync-maps.sh
```

**What this does:**
1. Validates map JSON files
2. Builds TypeScript (if `maps/src/` exists)
3. Syncs all files to S3 bucket
4. Sets correct content types and permissions

**Success looks like:**
- No validation errors
- "upload:" lines for each file
- No S3 errors

**Validation after sync:**
```bash
aws s3 ls s3://nfcore-hackathon-maps/default/ --profile nf-core
```

Should show `map.json` and tileset files.

---

## Validating Maps

Before syncing, validate the map files:

### Check JSON Syntax

```bash
python3 -m json.tool maps/default/map.json > /dev/null && echo "Valid JSON" || echo "Invalid JSON"
```

### Check for Common Errors

#### Empty Data Arrays (CRITICAL - WILL CRASH CLIENT)

The Phaser game engine crashes on empty `data` arrays in tile layers. Check:

```bash
grep -n '"data": \[\]' maps/default/map.json
```

**Success:** No output (no empty arrays).
**Problem:** If lines are returned, those layers have empty data arrays that will crash the client.

#### Tileset Path Validation

Tileset paths in the map must be relative paths that exist:

```bash
# Extract tileset paths from map
grep -o '"image": "[^"]*"' maps/default/map.json
```

Verify each path exists relative to the map file location.

#### Layer Property Syntax

Interactive zones use properties. Verify property format:

```bash
# Should show well-formed property objects
grep -A5 '"properties"' maps/default/map.json | head -20
```

---

## Building TypeScript Scripts

If the map has TypeScript scripts in `maps/src/`:

```bash
cd maps
npm install    # First time only
npm run build
```

**Success:** Creates `maps/dist/` with compiled JavaScript.

The `sync-maps.sh` script handles this automatically, but you can build manually to check for errors.

---

## Interactive Zone Properties

These properties create interactive behaviors when added to tile layers or objects in Tiled:

| Property | Type | Description |
|----------|------|-------------|
| `jitsiRoom` | string | Opens Jitsi video call with this room name |
| `silent` | boolean | Disables proximity audio in this zone |
| `openWebsite` | string | Opens URL when player enters |
| `playAudio` | string | Plays audio file from URL |
| `collides` | boolean | Blocks player movement |
| `startLayer` | boolean | Player spawn point |

### Example: Creating a Jitsi Meeting Room

In Tiled:
1. Create a tile layer or object
2. Add custom property: `jitsiRoom` = `meeting-room-1`
3. Save and sync

### Example: Creating a Silent Zone

1. Create a tile layer covering the area
2. Add custom property: `silent` = `true` (boolean)
3. Save and sync

---

## Troubleshooting

### Map Not Loading in Browser

**Check browser console** for errors (F12 → Console).

**Common causes:**

1. **Map file not in S3:**
   ```bash
   aws s3 ls s3://nfcore-hackathon-maps/default/map.json --profile nf-core
   ```
   Fix: Run `./scripts/sync-maps.sh`

2. **CORS error:**
   Check S3 bucket has correct CORS policy. The bucket should allow GET from any origin.

3. **Tileset not found (404):**
   Tileset paths in map.json must be relative and files must exist.
   ```bash
   # Check what paths the map references
   grep '"image":' maps/default/map.json
   ```

4. **Empty data array:**
   ```bash
   grep '"data": \[\]' maps/default/map.json
   ```
   Fix: Remove empty layers or add tile data in Tiled.

### Jitsi Zones Not Working

1. **Verify property name is exactly `jitsiRoom`** (case-sensitive)
2. **Verify property type is string** (not boolean or number)
3. **Check Jitsi service is healthy:** `./scripts/status.sh`

### Sync Fails with S3 Errors

1. **Access Denied:** Check AWS credentials are valid
   ```bash
   aws sts get-caller-identity --profile nf-core
   ```

2. **Bucket doesn't exist:** Infrastructure not deployed
   ```bash
   terraform state list | grep s3
   ```

3. **Network error:** Check internet connectivity

### TypeScript Build Fails

```bash
cd maps
npm run build 2>&1
```

Check the error message. Common issues:
- Missing dependencies: `npm install`
- Syntax errors in TypeScript files
- Type errors (fix the TypeScript code)

---

## Workflow Summary

### Human (in Tiled):
1. Edit `maps/default/map.json`
2. Add/modify tilesets, layers, properties
3. Save the file

### AI Agent (validation & sync):
1. Validate JSON syntax
2. Check for empty data arrays
3. Verify tileset paths exist
4. Build TypeScript if present
5. Run `./scripts/sync-maps.sh`
6. Verify files are in S3

### After Sync:
1. Refresh WorkAdventure in browser (may need hard refresh: Ctrl+Shift+R)
2. Test interactive zones work as expected
3. Commit map changes to git

---

## Important Reminders

1. **Always commit maps to git** - S3 is ephemeral
2. **Sync maps BEFORE first deploy** - WA needs OAuth templates on boot
3. **Never create empty data arrays** - Crashes Phaser engine
4. **Tileset paths must be relative** - Not absolute filesystem paths
5. **Test in browser after sync** - Visual verification is important
