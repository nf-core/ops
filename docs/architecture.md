# Architecture Overview

This document explains the architectural decisions and design rationale for the hackathon infrastructure.

## High-Level Architecture

```
                                    ┌─────────────────┐
                                    │   Route 53      │
                                    │ hackathon.nf-co.re
                                    └────────┬────────┘
                                             │
              ┌──────────────────────────────┼──────────────────────────────┐
              │                              │                              │
              ▼                              ▼                              ▼
    ┌─────────────────┐           ┌─────────────────┐           ┌─────────────────┐
    │  ALB (HTTPS)    │           │  EIP (LiveKit)  │           │  EIP (Jitsi)    │
    │ app.*, maps.*   │           │  livekit.*      │           │  jitsi.*        │
    └────────┬────────┘           └────────┬────────┘           └────────┬────────┘
             │                             │                             │
             ▼                             ▼                             ▼
    ┌─────────────────┐           ┌─────────────────┐           ┌─────────────────┐
    │ WorkAdventure   │           │ LiveKit Server  │           │ Jitsi Meet      │
    │ EC2 (t3.xlarge) │◄─────────►│ EC2 (c5.xlarge) │           │ EC2 (t3.medium) │
    │ Docker Compose  │           │ Caddy + LK      │           │ Docker Compose  │
    └────────┬────────┘           └─────────────────┘           └─────────────────┘
              │                             ▲
              │                             │
              │                    ┌────────┴────────┐
              │                    │  EIP (Coturn)   │
              │                    │  turn.*         │
              │                    └────────┬────────┘
              │                             │
              │                             ▼
              │                    ┌─────────────────┐
              │                    │ Coturn TURN     │
              │                    │ EC2 (t3.medium) │
              │                    └─────────────────┘
              │
              │  Maps served locally via nginx
              │  (cloned from git repo)
              ▼
```

## Service Roles

### WorkAdventure
The main user-facing application. A virtual office platform where hackathon participants can move around, see each other, and collaborate.

- **Why t3.xlarge?** Runs 7+ Docker containers including the game engine, requiring significant RAM (16GB)
- **Why ALB?** Handles TLS termination and allows multiple subdomains (app.*, maps.*, etc.)

### LiveKit
WebRTC media server providing proximity-based audio/video chat.

- **Why c5.xlarge?** LiveKit does real-time audio/video encoding. The c5 compute-optimized instance provides better CPU performance than general-purpose t3 instances.
- **Why EIP?** Direct IP needed for WebRTC connectivity (UDP ports 50000-60000)

### Coturn (TURN Server)
Relays WebRTC traffic for users behind restrictive NATs/firewalls.

- **Why needed?** Without TURN, some users (especially on corporate networks) cannot establish peer-to-peer video connections
- **Why t3.medium?** TURN is relay-only with low compute requirements

### Jitsi
Video conferencing for dedicated meeting rooms (triggered by map zones).

- **Why Ubuntu?** Jitsi requires specific Prosody packages from the Jitsi apt repository, which only supports Debian/Ubuntu
- **Why t3.medium?** Small meetings with modest load

## VPC Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                      VPC: 10.0.0.0/16                               │
│                      Name: nfcore-hackathon-vpc                     │
│                                                                     │
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐  │
│  │   Public Subnet 1           │  │   Public Subnet 2           │  │
│  │   10.0.1.0/24               │  │   10.0.2.0/24               │  │
│  │   eu-west-1a                │  │   eu-west-1b                │  │
│  │                             │  │                             │  │
│  │   ┌─────────────────┐       │  │                             │  │
│  │   │ All EC2         │       │  │   (ALB spans both subnets   │  │
│  │   │ Instances       │       │  │    for high availability)   │  │
│  │   └─────────────────┘       │  │                             │  │
│  └─────────────────────────────┘  └─────────────────────────────┘  │
│                    │                           │                    │
│                    └─────────────┬─────────────┘                    │
│                                  │                                  │
│                    ┌─────────────▼─────────────┐                    │
│                    │     Internet Gateway      │                    │
│                    └─────────────┬─────────────┘                    │
└──────────────────────────────────┼──────────────────────────────────┘
                                   │
                              Internet
```

### Why Two Subnets?
AWS Application Load Balancers require at least two subnets in different Availability Zones for high availability. All EC2 instances run in Subnet 1; Subnet 2 exists only to satisfy this ALB requirement.

### Why All Public Subnets?
For a temporary hackathon deployment, the simplicity of public subnets outweighs the marginal security benefit of private subnets + NAT gateways. SSH access is protected by 1Password-managed keys.

## Service Dependencies

```
WorkAdventure ──depends_on──▶ LiveKit
              ──depends_on──▶ Coturn
              ──depends_on──▶ Jitsi
```

This Terraform dependency chain means:
- LiveKit, Coturn, and Jitsi are created before WorkAdventure
- WorkAdventure's `user_data` script references the other services' endpoints
- Changes to any dependency can trigger WorkAdventure recreation (user_data hash changes)

**Practical implication:** Be careful with targeted operations. Destroying/recreating LiveKit, Coturn, or Jitsi may cascade to WorkAdventure.

## Video System Architecture

The stack has two independent video systems:

| Type | Provider | When Used | Behavior |
|------|----------|-----------|----------|
| **Proximity video** | LiveKit | Walking near other players | Auto-connects when close, fades with distance |
| **Meeting rooms** | Jitsi | Entering a `jitsiRoom` zone | Opens dedicated video call in overlay |
| **Silent zones** | N/A | Areas marked `silent: true` | Disables all audio/video |

## OAuth Flow

```
Internet → ALB (HTTPS:443)
              ↓
         EC2 Instance
              ↓
         Traefik (port 80)
              ↓
    ┌─────────┴─────────────┐
    ↓                       ↓
app.* subdomain        Other subdomains
    ↓                  (map-storage.*, uploader.*, icon.*)
oauth2-proxy                ↓
    ↓                  Direct to WA services
GitHub OAuth
    ↓
nf-core org check
    ↓
WorkAdventure (play:3000)
```

### WebSocket Bypass
Certain paths bypass oauth2-proxy entirely via Traefik routing:
- `/ws/*` → play:3001 (WebSocket, no auth)
- `/resources/*`, `/static/*` → play:3000 (static assets, no auth)

**Why?** oauth2-proxy doesn't properly handle WebSocket upgrade requests.

## DNS Structure

| Record | Type | Target | Purpose |
|--------|------|--------|---------|
| `app` | A (Alias) | ALB | WorkAdventure main |
| `play` | A (Alias) | ALB | WA alias |
| `maps` | A (Alias) | ALB | Map storage |
| `map-storage` | A (Alias) | ALB | Map storage (legacy) |
| `uploader` | A (Alias) | ALB | File uploads |
| `icon` | A (Alias) | ALB | Avatar icons |
| `livekit` | A | EIP | LiveKit server |
| `turn` | A | EIP | Coturn TURN |
| `jitsi` | A | EIP | Jitsi Meet |

## Port Reference

| Service | Ports | Protocol | Purpose |
|---------|-------|----------|---------|
| WorkAdventure | 80, 443 | TCP (via ALB) | Web interface |
| LiveKit | 443, 7880 | TCP | HTTPS API, WebRTC signaling |
| LiveKit | 50000-60000 | UDP | WebRTC media |
| Coturn | 3478 | UDP | TURN (unencrypted) |
| Coturn | 5349 | TCP | TURNS (TLS encrypted) |
| Jitsi | 80, 443, 4443 | TCP | Web, HTTPS, JVB fallback |
| Jitsi | 10000 | UDP | JVB media |
| All | 22 | TCP | SSH access |
