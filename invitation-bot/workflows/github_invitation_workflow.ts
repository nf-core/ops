import { DefineWorkflow, Schema } from "deno-slack-sdk/mod.ts";
import { GitHubInviteFunctionDefinition } from "../functions/github_invite_function.ts";
import { ExtractGitHubUsernameDefinition } from "../functions/extract_github_username.ts";

const GitHubInvitationWorkflow = DefineWorkflow({
  callback_id: "github_invitation_workflow",
  title: "GitHub Invitation Workflow",
  description: "Invites users to GitHub organization based on reactions",
  input_parameters: {
    properties: {
      user_id: {
        type: Schema.slack.types.user_id,
        description: "ID of the user who added the reaction",
      },
      channel_id: {
        type: Schema.slack.types.channel_id,
        description: "Channel where the reaction was added",
      },
      message_ts: {
        type: Schema.types.string,
        description: "Timestamp of the message that was reacted to",
      },
      reaction: {
        type: Schema.types.string,
        description: "The reaction that was added",
      },
    },
    required: ["user_id", "channel_id", "message_ts", "reaction"],
  },
});

// Step 1: Verify if the reaction is a checkmark
GitHubInvitationWorkflow.addStep(
  Schema.slack.functions.If,
  {
    condition: {
      left: "{{inputs.reaction}}",
      operator: "==",
      right: "white_check_mark",
    },
    then: GitHubInvitationWorkflow.addStep(
      Schema.slack.functions.GetConversationMessages,
      {
        channel_id: "{{inputs.channel_id}}",
        ts: "{{inputs.message_ts}}",
        limit: 1,
      }
    ).addStep(
      ExtractGitHubUsernameDefinition,
      {
        message_text: "{{steps.GetConversationMessages.outputs.messages[0].text}}",
      }
    ).addStep(
      GitHubInviteFunctionDefinition,
      {
        github_username: "{{steps.extract_github_username_function.outputs.github_username}}",
        inviter_user_id: "{{inputs.user_id}}",
      }
    ).addStep(
      Schema.slack.functions.PostMessage,
      {
        channel_id: "{{inputs.channel_id}}",
        thread_ts: "{{inputs.message_ts}}",
        message: "{{steps.github_invite_function.outputs.message}}",
      }
    ),
  }
);

export default GitHubInvitationWorkflow; 