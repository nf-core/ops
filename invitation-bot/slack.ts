import { SlackCLI } from "deno-slack-sdk/cli.ts";
import * as workflow from "./workflows/github_invitation_workflow.ts";

const cli = new SlackCLI();
cli.start();

console.log(`GitHub Invitation Bot started`); 