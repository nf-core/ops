# GitHub OAuth Setup

Configure GitHub OAuth for WorkAdventure authentication.

## Step 1: Create GitHub OAuth App

1. Go to: https://github.com/organizations/nf-core/settings/applications
2. Click **"New OAuth App"**
3. Fill in:

| Field                      | Value                                            |
| -------------------------- | ------------------------------------------------ |
| Application name           | `nf-core Hackathon WorkAdventure`                |
| Homepage URL               | `https://app.hackathon.nf-co.re`                 |
| Authorization callback URL | `https://app.hackathon.nf-co.re/oauth2/callback` |

4. Click **"Register application"**
5. Copy the **Client ID**
6. Click **"Generate a new client secret"** and copy immediately

## Step 2: Generate Cookie Secret

```bash
openssl rand -hex 16
```

**CRITICAL:** Must be exactly 32 hex characters (16 bytes). Do NOT use `-base64`.

## Step 3: Add to 1Password Environment

| Variable                     | Value                                      |
| ---------------------------- | ------------------------------------------ |
| `GITHUB_OAUTH_CLIENT_ID`     | From GitHub OAuth App                      |
| `GITHUB_OAUTH_CLIENT_SECRET` | From GitHub OAuth App                      |
| `OAUTH2_PROXY_COOKIE_SECRET` | From `openssl rand -hex 16` (32 hex chars) |

Remount environment after adding.

---

## How It Works

```
Browser → ALB → Traefik → oauth2-proxy → GitHub OAuth → nf-core org check → WorkAdventure
```

### Routes That Bypass Auth

- `/ws/*` → play:3001 (WebSocket - oauth2-proxy can't handle WebSocket upgrades)
- `/resources/*`, `/static/*` → play:3000 (game assets)

### oauth2-proxy Settings

| Setting                               | Value                 |
| ------------------------------------- | --------------------- |
| `--provider=github`                   | OAuth provider        |
| `--github-org=nf-core`                | Required organization |
| `--cookie-domain=.hackathon.nf-co.re` | Cookie scope          |

---

## Troubleshooting

### "Access Denied" for nf-core Members

Organization membership must be **public**:

1. Go to https://github.com/orgs/nf-core/people
2. Find user, change visibility to "Public"

### Redirect Loop

1. Clear all cookies for `*.hackathon.nf-co.re` and `github.com`
2. Try incognito mode
3. Check oauth2-proxy logs:
   ```bash
   ./scripts/ssh.sh wa
   docker compose logs oauth2-proxy
   ```

### oauth2-proxy Not Starting

```bash
./scripts/ssh.sh wa
docker ps -a | grep oauth2-proxy
docker compose logs oauth2-proxy
```

Common errors:

- "invalid cookie secret" → Wrong format (use `openssl rand -hex 16`)
- "invalid client id/secret" → Check GitHub OAuth App values

### WebSocket Errors

WebSocket uses port **3001**, not 3000:

```bash
./scripts/ssh.sh wa
docker logs docker-reverse-proxy-1 | grep -i websocket
```

---

## Testing OAuth Flow

1. Open https://app.hackathon.nf-co.re in **incognito mode**
2. Should redirect to GitHub login
3. Log in as nf-core member → Should enter WorkAdventure
4. Log in as non-member → Should see custom "Access Denied" page

### Verify Cookies

Browser DevTools → Application → Cookies:

- `_oauth2_proxy` for `.hackathon.nf-co.re`
- Should be `Secure` and `HttpOnly`
