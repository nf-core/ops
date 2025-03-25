import { Trigger } from "deno-slack-sdk/types.ts";
import { TriggerContextData, TriggerTypes } from "deno-slack-api/mod.ts";
import GitHubInvitationWorkflow from "../workflows/github_invitation_workflow.ts";

/**
 * This trigger creates a shortcut for the GitHub invitation workflow
 */
const githubInvitationTrigger: Trigger<typeof GitHubInvitationWorkflow.definition> = {
  type: TriggerTypes.Shortcut,
  name: "Invite to GitHub Repository",
  description: "Invite a user to a GitHub repository",
  workflow: `#/workflows/${GitHubInvitationWorkflow.definition.callback_id}`,
  inputs: {
    github_username: {
      value: "{{data.github_username}}",
    },
    repository: {
      value: "{{data.repository}}",
    },
    permission_level: {
      value: "{{data.permission_level}}",
    },
  },
};

export default githubInvitationTrigger; 