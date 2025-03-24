import { DefineFunction, Schema, SlackFunction } from "deno-slack-sdk/mod.ts";

export const GitHubInviteFunctionDefinition = DefineFunction({
  callback_id: "github_invite_function",
  title: "Invite to GitHub Organization",
  description: "Sends an invitation to join the GitHub organization",
  source_file: "functions/github_invite_function.ts",
  input_parameters: {
    properties: {
      github_username: {
        type: Schema.types.string,
        description: "GitHub username to invite",
      },
      inviter_user_id: {
        type: Schema.slack.types.user_id,
        description: "Slack user ID of the person who initiated the invitation",
      },
    },
    required: ["github_username"],
  },
  output_parameters: {
    properties: {
      success: {
        type: Schema.types.boolean,
        description: "Whether the invitation was sent successfully",
      },
      message: {
        type: Schema.types.string,
        description: "Status message about the invitation",
      },
    },
    required: ["success", "message"],
  },
});

export default SlackFunction(
  GitHubInviteFunctionDefinition,
  async ({ inputs, client, env }) => {
    const { github_username, inviter_user_id } = inputs;
    console.log(`Sending GitHub invitation to ${github_username}`);
    
    try {
      // Get the GitHub token from environment variables
      const githubToken = env.GITHUB_TOKEN;
      const githubOrg = env.GITHUB_ORG;
      
      if (!githubToken || !githubOrg) {
        return {
          outputs: {
            success: false,
            message: "GitHub configuration is missing. Please set GITHUB_TOKEN and GITHUB_ORG environment variables.",
          },
        };
      }
      
      // Get inviter info for the notification
      let inviterName = "Someone";
      if (inviter_user_id) {
        try {
          const userInfo = await client.users.info({ user: inviter_user_id });
          if (userInfo.ok && userInfo.user) {
            inviterName = userInfo.user.real_name || userInfo.user.name || "Someone";
          }
        } catch (error) {
          console.error("Error fetching user info:", error);
        }
      }

      // Send invitation to GitHub organization using GitHub API
      const response = await fetch(`https://api.github.com/orgs/${githubOrg}/invitations`, {
        method: "POST",
        headers: {
          "Accept": "application/vnd.github+json",
          "Authorization": `Bearer ${githubToken}`,
          "X-GitHub-Api-Version": "2022-11-28",
        },
        body: JSON.stringify({
          email: null,  // Using username instead of email
          role: "direct_member",  // Default role, can be customized
          invitee_id: null,  // Not using ID
          team_ids: [],  // No specific teams
          login: github_username,  // GitHub username to invite
        }),
      });

      if (response.status === 201) {
        return {
          outputs: {
            success: true,
            message: `✅ ${inviterName} has invited @${github_username} to join the ${githubOrg} GitHub organization.`,
          },
        };
      } else {
        const errorData = await response.json();
        console.error("GitHub API error:", errorData);
        
        // Handle specific error cases
        if (response.status === 422 && errorData.message?.includes("already a member")) {
          return {
            outputs: {
              success: false,
              message: `@${github_username} is already a member of the ${githubOrg} organization.`,
            },
          };
        } else if (response.status === 422 && errorData.message?.includes("already invited")) {
          return {
            outputs: {
              success: false,
              message: `@${github_username} already has a pending invitation to the ${githubOrg} organization.`,
            },
          };
        } else if (response.status === 404) {
          return {
            outputs: {
              success: false,
              message: `Could not find GitHub user @${github_username}. Please verify the username.`,
            },
          };
        }
        
        return {
          outputs: {
            success: false,
            message: `Failed to invite @${github_username}: ${errorData.message || "Unknown error"}`,
          },
        };
      }
    } catch (error) {
      console.error("Error inviting to GitHub:", error);
      return {
        outputs: {
          success: false,
          message: `Error inviting @${github_username}: ${error.message || "Unknown error"}`,
        },
      };
    }
  },
); 