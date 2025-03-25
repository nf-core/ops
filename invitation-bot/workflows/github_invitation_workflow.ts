import { DefineWorkflow, Schema } from "deno-slack-sdk/mod.ts";
import { GitHubInvitationFunction } from "../functions/github_invitation.ts";

/**
 * This workflow defines a custom step for Workflow Builder 
 * that allows users to invite people to GitHub repositories.
 */
const GitHubInvitationWorkflow = DefineWorkflow({
  callback_id: "github_invitation_workflow",
  title: "Invite to GitHub Repository",
  description: "Send an invitation to join a GitHub repository",
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
});

// Add a step that uses our custom function
GitHubInvitationWorkflow.addStep(GitHubInvitationFunction, {
  github_username: GitHubInvitationWorkflow.inputs.github_username,
  repository: GitHubInvitationWorkflow.inputs.repository,
  permission_level: GitHubInvitationWorkflow.inputs.permission_level,
});

export default GitHubInvitationWorkflow; 