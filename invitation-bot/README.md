# GitHub Invitation Bot for Slack

A Slack bot that automates GitHub organization invitations based on reactions in Slack.

## Features

- Monitors for checkmark reactions (✅) on messages
- Verifies if the person adding the reaction is in the authorized user group
- Extracts GitHub username from the original message
- Sends an invitation to the GitHub organization
- Provides confirmation in the thread

## Setup

### Prerequisites

1. [Slack CLI](https://api.slack.com/automation/cli) installed
2. A GitHub organization and a personal access token with organization admin permissions

### Installation

1. Clone this repository
2. Run `slack run` to start the app in development mode
3. Set environment variables:
   - `GITHUB_TOKEN`: Your GitHub personal access token
   - `GITHUB_ORG`: The name of your GitHub organization

## Configuration

### Channel Configuration

By default, the bot monitors reactions in all channels it's added to. You can configure specific channels in the `triggers/reaction_added_trigger.ts` file.

### Authorized Users

You can restrict who can add reactions to trigger invitations by implementing authorization logic in the workflow.

## Usage

1. Post a message mentioning a GitHub username (e.g., "Please add @username to our GitHub organization")
2. Add a ✅ reaction to the message
3. The bot will automatically extract the GitHub username and send an invitation
4. A confirmation message will be posted in the thread

## GitHub Username Detection

The bot will try to extract GitHub usernames from messages in the following formats:

- GitHub: username
- GitHub username: username
- @username on GitHub
- github.com/username

If none of these patterns match, it will try to identify potential usernames in the message.