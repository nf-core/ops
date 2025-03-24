import { Trigger } from "deno-slack-api/types.ts";
import { TriggerTypes } from "deno-slack-api/mod.ts";
import GitHubInvitationWorkflow from "../workflows/github_invitation_workflow.ts";

const reactionAddedTrigger: Trigger<typeof GitHubInvitationWorkflow.definition> = {
  type: TriggerTypes.Event,
  name: "Reaction Added Trigger",
  description: "Triggers when a reaction is added to a message",
  workflow: `#/workflows/${GitHubInvitationWorkflow.definition.callback_id}`,
  event: {
    event_type: "slack#/events/reaction_added",
    channel_ids: ["YOUR_CHANNEL_ID_HERE"], // Replace with your channel IDs or set during installation
  },
  inputs: {
    user_id: { value: "{{data.user_id}}" },
    channel_id: { value: "{{data.channel_id}}" },
    message_ts: { value: "{{data.message_ts}}" },
    reaction: { value: "{{data.reaction}}" },
  },
};

export default reactionAddedTrigger; 