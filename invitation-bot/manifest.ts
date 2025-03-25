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
    org_deploy_enabled: true,
    socket_mode_enabled: true,
    function_runtime: "remote",
    event_subscriptions: {
      bot_events: ["function_executed"]
    },
    interactivity: {
      is_enabled: true
    }
  },
  functions: {
    github_invitation_function: {
      title: "Invite to GitHub Repository",
      description: "Invite a user to a GitHub repository",
      input_parameters: {
        github_username: {
          type: "string",
          description: "GitHub username to invite"
        },
        repository: {
          type: "string",
          description: "GitHub repository name (e.g., 'organization/repo')"
        },
        permission_level: {
          type: "string",
          description: "Permission level (read, write, admin)",
          enum: ["read", "write", "admin"],
          default: "read"
        }
      },
      output_parameters: {
        success: {
          type: "boolean",
          description: "Whether the invitation was successful"
        },
        message: {
          type: "string",
          description: "Message about the invitation result"
        }
      }
    }
  }
};

// Output the manifest as JSON for the Slack CLI
console.log(JSON.stringify(manifest, null, 2));
