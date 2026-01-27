# Branding and Customization

Guide to customizing the WorkAdventure deployment with organization branding.

## Assets Structure

```
assets/
├── logos/
│   ├── nf-core-logo.png           # Wide logo (general use)
│   ├── nf-core-logo-square.png    # Square logo (server icon)
│   └── nf-core-logo-darkbg.png    # Wide logo for dark backgrounds
└── templates/
    ├── sign_in.html               # Custom OAuth sign-in page
    └── error.html                 # Access denied error page
```

Assets are served locally via nginx on the WorkAdventure instance from the cloned hackathon-infra repo.

## Server Branding

Configured in `terraform/modules/workadventure/templates/user_data.sh`:

| Setting | Value | Purpose |
|---------|-------|---------|
| `SERVER_NAME` | `nf-core Hackathon` | Displayed in UI |
| `SERVER_MOTD` | Welcome message | Message of the day |
| `SERVER_ICON` | Local URL to square logo | Server icon in listings |
| `CONTACT_URL` | nf-core Slack URL | Help/contact link |

## Custom Sign-In Page

The `sign_in.html` template provides:

### Social Sharing Meta Tags
When the WorkAdventure URL is shared on Slack, Twitter, LinkedIn, etc., it shows organization branding:

```html
<!-- Open Graph -->
<meta property="og:title" content="nf-core Hackathon">
<meta property="og:description" content="Join the nf-core hackathon virtual workspace">
<meta property="og:image" content="https://app.hackathon.nf-co.re/assets/logos/nf-core-logo.png">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="nf-core Hackathon">
```

### Styling
The sign-in page uses nf-core colors with a dark theme and GitHub-styled sign-in button.

## Custom Error Page

The `error.html` template is shown when:
- User is not a member of nf-core GitHub org
- User's org membership is private (not public)
- OAuth flow fails

It includes clear explanation of access requirements and a link to make org membership public.

## Customizing for Different Events

### Change Organization Branding

1. Replace logos in `assets/logos/`:
   - Wide logo (transparent background)
   - Square logo (for server icon)
   - Dark background version (for sign-in page)

2. Update `sign_in.html`:
   - Change meta tags
   - Update logo image path
   - Modify welcome text

3. Update `error.html`:
   - Change branding
   - Update organization name

4. Commit changes and sync: `git push && ./scripts/sync-maps.sh`

### Change Server Name

Edit `terraform/modules/workadventure/templates/user_data.sh`:
```bash
SERVER_NAME="Your Event Name"
SERVER_MOTD="Welcome message here"
```

Then apply: `terraform apply`

### Change Contact URL

Edit `terraform/modules/workadventure/templates/user_data.sh`:
```bash
CONTACT_URL="https://your-help-url.com"
```

## Asset URLs

After deployment, assets are available at:
```
https://app.hackathon.nf-co.re/assets/logos/nf-core-logo.png
https://app.hackathon.nf-co.re/assets/logos/nf-core-logo-square.png
```

## Testing Social Sharing

After deploying, test social sharing previews:

1. **Slack**: Paste `https://app.hackathon.nf-co.re` in a message
2. **Twitter**: Use [Twitter Card Validator](https://cards-dev.twitter.com/validator)
3. **Facebook**: Use [Sharing Debugger](https://developers.facebook.com/tools/debug/)
4. **LinkedIn**: Use [Post Inspector](https://www.linkedin.com/post-inspector/)

If previews don't show correctly:
- Verify asset URLs are accessible
- Clear cache on the respective platform's debugger
