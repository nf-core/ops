import { Manifest } from "deno-slack-sdk/mod.ts";
import GitHubInvitationWorkflow from "./workflows/github_invitation_workflow.ts";
import { ExtractGitHubUsernameDefinition } from "./functions/extract_github_username.ts";
import { GitHubInviteFunctionDefinition } from "./functions/github_invite_function.ts";

export default Manifest({
  name: "GitHub Invitation Bot",
  description: "Automates GitHub organization invitations based on reactions in Slack",
  icon: "assets/icon.png",
  workflows: [GitHubInvitationWorkflow],
  functions: [GitHubInviteFunctionDefinition, ExtractGitHubUsernameDefinition],
  outgoingDomains: ["api.github.com"],
  botScopes: [
    "channels:history",
    "chat:write",
    "reactions:read",
    "users:read",
    "users:read.email",
  ],
}); 