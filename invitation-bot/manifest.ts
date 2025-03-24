// Simple manifest generator for Slack CLI
const manifest = {
  display_information: {
    name: "Invitation Bot",
    description: "A GitHub invitation bot for nf-core",
    background_color: "#4A154B"
  },
  features: {
    bot_user: {
      display_name: "Invitation Bot",
      always_online: true
    }
  },
  oauth_config: {
    scopes: {
      bot: [
        "commands",
        "chat:write",
        "chat:write.public",
        "reactions:read"
      ]
    }
  },
  settings: {
    org_deploy_enabled: false,
    socket_mode_enabled: true
  }
};

// Output the manifest as JSON for the Slack CLI
console.log(JSON.stringify(manifest, null, 2));
