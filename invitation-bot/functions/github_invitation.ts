import { DefineFunction, Schema, SlackFunction } from "deno-slack-sdk/mod.ts";

/**
 * This function allows users to invite someone to a GitHub repository
 * It can be used as a custom step in Workflow Builder
 */
export const GitHubInvitationFunction = DefineFunction({
  callback_id: "github_invitation_function",
  title: "Invite to GitHub Repository",
  description: "Invite a user to a GitHub repository",
  source_file: "functions/github_invitation_handler.ts",
  input_parameters: {
    properties: {
      github_username: {
        type: Schema.types.string,
        description: "GitHub username to invite",
      },
      repository: {
        type: Schema.types.string,
        description: "GitHub repository name (e.g., 'organization/repo')",
      },
      permission_level: {
        type: Schema.types.string,
        description: "Permission level (read, write, admin)",
        enum: ["read", "write", "admin"],
        default: "read",
      },
    },
    required: ["github_username", "repository"],
  },
  output_parameters: {
    properties: {
      success: {
        type: Schema.types.boolean,
        description: "Whether the invitation was successful",
      },
      message: {
        type: Schema.types.string,
        description: "Message about the invitation result",
      },
    },
    required: ["success", "message"],
  },
}); 