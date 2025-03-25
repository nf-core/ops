# GitHub Invitation Bot for nf-core

A Slack app that provides a custom Workflow Builder step to invite people to GitHub repositories.

## Features

- Custom Workflow Builder step to invite users to GitHub repositories
- Configurable permission levels (read, write, admin)

## Setup Instructions

1. The app is now configured with a custom function for GitHub repository invitations
2. To complete the setup and make the function available in Workflow Builder:

```bash
# Deploy the app to your workspace (select your app when prompted)
slack deploy

# After deployment completes, trigger creation (select your app when prompted)
slack trigger create
```

3. When creating the trigger, you'll be asked to select the workflow. Choose to create a new trigger for the "Invite to GitHub Repository" workflow.

4. After the trigger is created, you'll receive a URL that can be used in Slack to trigger the workflow.

## Using the Custom Step in Workflow Builder

1. Go to your Slack workspace
2. Open Workflow Builder (click on your workspace name > Tools > Workflow Builder)
3. Create a new workflow or edit an existing one
4. Add a step and search for "Invite to GitHub Repository" in the steps search bar
5. Configure the step with:
   - GitHub username
   - Repository name
   - Permission level (read, write, or admin)

## Troubleshooting

If you encounter validation errors:

```bash
# Test the manifest format
slack manifest test

# Validate the manifest for your specific app
slack manifest validate -a YOUR_APP_ID
```

## License

[MIT](LICENSE)