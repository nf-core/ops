# WorkAdventure Maps

Custom maps for the nf-core hackathon, based on the [WorkAdventure hackathon template](https://github.com/workadventure/hackathon).

## Important: Source of Truth

The `maps/` folder in this repository is the **source of truth** for all map assets. Maps are served directly from the cloned repository on the EC2 instance.

**Always commit map changes to git** before tearing down infrastructure.

## Workflow

- **Humans:** Edit maps using Tiled Map Editor (this guide)
- **AI Agents:** Validate maps and sync to server (see `.claude/skills/maps/SKILL.md`)

## Quick Start

### Prerequisites

- [Tiled Map Editor](https://www.mapeditor.org/) (free, cross-platform)

### Edit and Deploy

```bash
# 1. Open the map in Tiled
open maps/default/map.json   # macOS
# Or: File > Open in Tiled

# 2. Make your changes in Tiled and save

# 3. If you modified TypeScript scripts, rebuild locally
cd maps/default && npm run build && cd ../..

# 4. Commit and push your changes
git add maps/
git commit -m "Update maps"
git push

# 5. Sync to the server
./scripts/sync-maps.sh
```

## Directory Structure

```
maps/
├── README.md              # This file
└── default/               # Main hackathon map
    ├── map.json           # Map file (Tiled JSON format)
    ├── src/               # TypeScript source for scripting
    │   ├── main.ts        # Main script source
    │   └── index.html     # HTML wrapper for WorkAdventure API
    ├── dist/              # Pre-built scripts (committed to git)
    │   ├── index.html     # Built HTML with iframe API
    │   └── main.js        # Compiled JavaScript
    ├── package.json       # NPM dependencies
    ├── vite.config.ts     # Build configuration
    ├── tsconfig.json      # TypeScript configuration
    └── assets/            # Tileset images and audio
        ├── *.png          # Tileset images
        ├── *.mp3          # Background music
        └── *.wav          # Sound effects
```

## Map Scripting

Interactive features are implemented using the [WorkAdventure Scripting API](https://docs.workadventu.re/developer/map-scripting/).

The script provides:
- **Welcome message** - Displays when users enter the map
- **Help zone popup** - Links to Slack, Documentation, GitHub (triggered by `needHelp` zone)
- **Social links popup** - Links to Mastodon, Bluesky, YouTube, LinkedIn (triggered by `followUs` zone)
- **Hackathon info popup** - Links to events, projects, guidelines (triggered by `hackathonInfo` zone)

### Script Architecture

The script is built using TypeScript and Vite:
- **Source**: `src/main.ts` - TypeScript with WorkAdventure API types
- **Wrapper**: `src/index.html` - Loads WorkAdventure iframe API before script
- **Output**: `dist/` - Pre-built HTML and JS files (committed to git, served as `script/`)

The HTML wrapper is required because WorkAdventure scripts run in an iframe and need the [iframe_api.js](https://play.workadventu.re/iframe_api.js) to communicate with the main WorkAdventure window.

### Building the Script

The `dist/` folder is **committed to git** and contains pre-built scripts. Only rebuild if you modify TypeScript:

```bash
cd maps/default

# Install dependencies (first time only)
npm install

# Build to dist/
npm run build

# Commit the built files
git add dist/
git commit -m "Rebuild map scripts"
```

For development with hot reload:
```bash
npm run dev
```

### Adding Interactive Zones

To add interactive zones to the map:
1. In Tiled, create an Object Layer
2. Draw a rectangle where you want the interaction
3. Set the object's `name` property to match the zone name in your script (e.g., `needHelp`)
4. Add the zone handler in `src/main.ts` using `WA.room.area.onEnter()`
5. Rebuild scripts if needed, commit, and sync

### How It Works

When the map loads:
1. WorkAdventure reads the `script` property from `map.json` (points to `script/index.html`)
2. WorkAdventure loads the HTML in a sandboxed iframe
3. The HTML loads `iframe_api.js` which provides the global `WA` object
4. The HTML loads `main.js` which uses `WA` to interact with the map

## Editing Maps in Tiled

### Opening the Map

1. Install [Tiled](https://www.mapeditor.org/) (free)
2. Open `maps/default/map.json`
3. The map and all tilesets should load automatically

### Understanding Layers

Layers render from bottom to top. The hackathon map has this structure:

```
Layers panel (top = rendered last):
├── abovePlayer/          # Group: rendered above characters
│   ├── ceiling
│   └── furniture-top
├── floorLayer            # REQUIRED: characters render at this level
├── walls                 # Collision layer
├── furniture             # Desks, chairs, etc.
├── floor                 # Base floor tiles
└── zones/                # Group: interactive zones
    ├── start             # Spawn points (startLayer property)
    ├── silent            # Quiet zones
    └── jitsi-*           # Meeting rooms
```

**Important:** The `floorLayer` (or a layer with `startLayer: true`) is required for character rendering and spawning.

### Placing Furniture

1. **Select a tileset** from the Tilesets panel (bottom-right)
2. **Select tiles** by clicking/dragging on the tileset
3. **Select a layer** in the Layers panel
4. **Paint** using the Stamp Brush tool (B) or fill with Bucket Fill (F)

**Tips:**
- Furniture that should appear above players goes in `abovePlayer/` group
- Furniture below players goes in `furniture` layer
- Add `collides: true` to tiles that block movement

### Adding Collisions

To make tiles solid (players can't walk through):

**Method 1: Per-tile (recommended)**
1. Select a tileset in the Tilesets panel
2. Click "Edit Tileset" (wrench icon)
3. Select the tile(s) to make solid
4. In Properties panel, add: `collides` (bool) = `true`

**Method 2: Per-layer**
1. Create a new tile layer named `collisions`
2. Add property: `collides` = `true`
3. Paint blocking tiles on this layer (they'll be invisible in-game)

### Creating Interactive Zones

Create zones by adding objects with special properties:

1. Create or select an **Object Layer**
2. Use Rectangle tool (R) to draw a zone
3. Add properties to the object (see table below)

## Interactive Properties Reference

Add these as custom properties on tiles, objects, or layers:

### Movement & Collision

| Property | Type | Description |
|----------|------|-------------|
| `collides` | bool | Blocks player movement |
| `start` | bool | Legacy spawn point (use `startLayer` instead) |
| `startLayer` | bool | Marks layer as spawn area |

### Audio & Video

| Property | Type | Description |
|----------|------|-------------|
| `playAudio` | string | URL/path to background audio |
| `playAudioLoop` | bool | Loop the audio (default: true) |
| `silent` | bool | Mutes proximity video/audio in zone |
| `jitsiRoom` | string | Jitsi meeting room name |
| `jitsiTrigger` | string | `onaction` = click to join, else auto-join |
| `jitsiWidth` | int | Jitsi iframe width (%) |

### Web Integration

| Property | Type | Description |
|----------|------|-------------|
| `openWebsite` | string | URL to open in iframe |
| `openWebsiteTrigger` | string | `onaction` = click to open |
| `openWebsiteAllowApi` | bool | Allow WorkAdventure scripting API |
| `openTab` | string | URL to open in new browser tab |

### Navigation

| Property | Type | Description |
|----------|------|-------------|
| `exitUrl` | string | Teleport to another map (full URL) |
| `exitSceneUrl` | string | Teleport to map on same server (relative path) |

### Examples

**Meeting room zone:**
```
Object properties:
  jitsiRoom: "standup-room"
  jitsiTrigger: "onaction"
```

**Website kiosk:**
```
Object properties:
  openWebsite: "https://nf-co.re"
  openWebsiteTrigger: "onaction"
```

**Quiet zone (no proximity chat):**
```
Layer or object property:
  silent: true
```

**Background music area:**
```
Object properties:
  playAudio: "assets/bensound-thelounge.mp3"
  playAudioLoop: true
```

## Video Chat Architecture

This deployment uses two video systems:

### 1. Proximity Video (LiveKit)

- Walk near another player (within ~4 tiles)
- Video/audio automatically starts
- Walk away to disconnect
- Muted in zones with `silent: true`

### 2. Meeting Rooms (Jitsi)

- Create zones with `jitsiRoom` property
- Players in zone join isolated video room
- Good for presentations, standups, focused discussions

## Testing Locally

```bash
# Start local HTTP server
cd maps
python3 -m http.server 8080

# In browser, construct URL:
# https://app.hackathon.nf-co.re/_/global/localhost:8080/default/map.json
#
# Note: Local testing requires HTTPS. For quick checks, just sync to server.
```

## Deploying

```bash
# Commit and push your changes first
git add maps/
git commit -m "Update maps"
git push

# Sync to the server (does git pull on EC2)
./scripts/sync-maps.sh
```

Changes are live immediately after sync. Users may need to hard refresh (Ctrl+Shift+R).

## Validation

Maps are validated before syncing. To validate without syncing:

```bash
./scripts/validate-maps.sh
```

Checks performed:
- JSON syntax is valid
- All tileset images exist
- Start/spawn layer is present
- Tile size is 32x32

## Troubleshooting

### Map not loading / Blue screen

```bash
# Check the map URL is accessible
curl -I https://app.hackathon.nf-co.re/maps/default/map.json

# Sync the latest changes
./scripts/sync-maps.sh
```

### Tiles not rendering

1. Check tileset paths are relative (e.g., `assets/tileset.png`)
2. Verify tileset files exist in `maps/default/assets/`
3. Check browser Network tab for 404 errors

### Tilesets not loading in Tiled

If Tiled shows red X for tilesets:
1. Ensure you opened `map.json` from the `maps/default/` directory
2. Check that `assets/` folder contains all PNG files
3. Verify tileset paths in map.json match actual filenames

### Validation fails

```bash
# Run validation to see detailed errors
./scripts/validate-maps.sh

# Common fixes:
# - Missing tileset: add the PNG to assets/
# - Invalid JSON: check for trailing commas, syntax errors
# - No start layer: add startLayer property to a layer
```

## Tileset Resources

The hackathon map includes LimeZu modern interior tilesets. For additional assets:

- [LimeZu on itch.io](https://limezu.itch.io/) - Modern interiors (used in this map)
- [OpenGameArt](https://opengameart.org/) - Free assets
- [itch.io Tilesets](https://itch.io/game-assets/tag-tileset) - Search "office", "interior"
- [Kenney Assets](https://kenney.nl/assets) - Free game assets

**Requirements for new tilesets:**
- PNG format
- 32x32 pixel tiles
- Place in `maps/default/assets/`
- Add to map via Map > New Tileset in Tiled

## Design Guidelines

### Recommended Areas

- Lobby/entrance with welcome info
- Help desk area
- Breakout rooms (small meeting spaces)
- Quiet zone (silent area for focused work)
- Social/coffee area
- Presentation space (Jitsi room)

### nf-core Branding

- Primary Green: #24B064
- Background: #1A1A1A
- Consider adding nf-core logos/posters using custom tilesets

### Performance Tips

- Keep tileset count reasonable (map has 15, which is fine)
- Avoid excessive animated tiles
- Use compressed PNG images
- Test with multiple concurrent users
