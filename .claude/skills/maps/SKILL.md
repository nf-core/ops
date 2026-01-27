---
name: maps
description: >
  Validate and sync WorkAdventure maps. Use when working with map files,
  syncing changes, checking for map errors, or setting up interactive zones
  (Jitsi rooms, silent areas). Covers JSON validation, TypeScript builds,
  and troubleshooting map loading issues.
---

# Maps: Validate and Sync

This skill covers validating and syncing WorkAdventure maps. 

**Important workflow note:** Map editing is done by humans using the Tiled Map Editor. AI agents assist with validation, building TypeScript scripts, and syncing to the server.

For map editing instructions, see `maps/README.md`.

## Map Architecture Overview

```
maps/                          # Local source (tracked in git)
├── default/
│   ├── map.json              # Main map file (edited in Tiled)
│   ├── tilesets/             # Tileset images
│   └── src/                  # TypeScript scripts
│       └── main.ts
│   └── dist/                 # Pre-built scripts (committed to git, symlinked to script/)

        ↓ sync-maps.sh ↓

EC2: /opt/workadventure/hackathon-infra/  # Cloned repo on server
├── maps/                                  # Served via nginx at /maps/*
└── assets/                                # Served via nginx at /assets/*
```

**Key points:**
- Maps are served **locally from the EC2 instance** via nginx (same origin as app)
- The `hackathon-infra` repo is cloned during deployment
- `sync-maps.sh` SSHs into the server and runs `git pull`
- **Always commit map changes to git** before syncing

---

## Pre-Sync Checklist

### 1. Verify Environment

```bash
./scripts/validate-env.sh
```

### 2. Ensure Changes Are Committed and Pushed

```bash
git status
git add maps/
git commit -m "Update maps"
git push
```

**Important:** The sync script pulls from git, so changes must be pushed first.

---

## Sync Maps to Server

```bash
./scripts/sync-maps.sh
```

**What this does:**
1. SSHs into the WorkAdventure EC2 instance
2. Runs `git pull` to get latest changes
3. Maps are immediately available (no container restart needed)

**Success looks like:**
- "Pulling latest changes..."
- "Maps updated successfully!"

**After sync:** Users may need to hard refresh their browser (Ctrl+Shift+R) to see changes.

---

## Validating Maps

Before syncing, validate the map files:

### Check JSON Syntax

```bash
python3 -m json.tool maps/default/map.json > /dev/null && echo "Valid JSON" || echo "Invalid JSON"
```

### Check for Common Errors

#### Empty Data Arrays (CRITICAL - WILL CRASH CLIENT)

The Phaser game engine crashes on empty `data` arrays in tile layers:

```bash
grep -n '"data": \[\]' maps/default/map.json
```

**Success:** No output (no empty arrays).

#### Tileset Path Validation

Tileset paths in the map must be relative paths that exist:

```bash
grep -o '"image": "[^"]*"' maps/default/map.json
```

---

## Building TypeScript Scripts

The `dist/` folder is **committed to git** and contains pre-built scripts. You only need to rebuild locally if you modify `maps/default/src/main.ts`:

```bash
cd maps/default
npm install    # First time only
npm run build
git add dist/
git commit -m "Rebuild map scripts"
```

**Important:** Always commit the updated `dist/` folder after rebuilding.

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
| `focusable` | boolean | Makes area appear in Explorer and auto-zooms camera |

### Example: Creating a Jitsi Meeting Room

In Tiled:
1. Create a tile layer or object
2. Add custom property: `jitsiRoom` = `meeting-room-1`
3. Save and sync

### Example: Creating a Focusable Area

In Tiled (must be a **rectangle object**, not a tile layer):
1. Select floorLayer in the Objects panel
2. Use Rectangle tool (R) to draw over the area
3. Name it descriptively (e.g., "Meeting Room - Alpha")
4. Add custom property: `focusable` = `true` (boolean)
5. Save and sync

---

## Troubleshooting

### Map Not Loading in Browser

**Check browser console** for errors (F12 → Console).

**Common causes:**

1. **Changes not pushed to git:**
   ```bash
   git status
   ```
   Fix: Commit and push, then run `./scripts/sync-maps.sh`

2. **Tileset not found (404):**
   Tileset paths in map.json must be relative and files must exist.

3. **Empty data array:**
   ```bash
   grep '"data": \[\]' maps/default/map.json
   ```
   Fix: Remove empty layers or add tile data in Tiled.

### Jitsi Zones Not Working

1. **Verify property name is exactly `jitsiRoom`** (case-sensitive)
2. **Verify property type is string** (not boolean or number)
3. **Check Jitsi service is healthy:** `./scripts/status.sh`

### Sync Fails

1. **SSH connection fails:** Check your SSH key and that the EC2 instance is running
2. **Git pull fails:** Ensure you've pushed your changes first

### TypeScript Build Fails (local)

If you modify `maps/default/src/main.ts`, rebuild locally before committing:

```bash
cd maps/default
npm install    # First time only
npm run build
```

Then commit the updated `dist/` folder along with your changes.

---

## Workflow Summary

### Human (in Tiled):
1. Edit `maps/default/map.json`
2. Add/modify tilesets, layers, properties
3. Save the file

### AI Agent (validation & sync):
1. Validate JSON syntax
2. Check for empty data arrays
3. If TypeScript changed: build locally, commit `dist/`
4. Commit and push to git
5. Run `./scripts/sync-maps.sh`
6. Verify in browser

### After Sync:
1. Hard refresh WorkAdventure in browser (Ctrl+Shift+R)
2. Test interactive zones work as expected

---

## Important Reminders

1. **Always commit and push before sync** - Server pulls from git
2. **Never create empty data arrays** - Crashes Phaser engine
3. **Tileset paths must be relative** - Not absolute filesystem paths
4. **Test in browser after sync** - Visual verification is important
5. **Map scripts run in iframe** - Cannot directly manipulate parent UI
