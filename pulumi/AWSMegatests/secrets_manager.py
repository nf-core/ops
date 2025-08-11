"""Configuration management for AWS Megatests infrastructure using Pulumi ESC"""

import os


def get_configuration():
    """Get configuration values from ESC environment variables"""

    # All configuration comes from ESC environment variables
    # These are automatically set when the ESC environment is imported

    # Get workspace ID from environment or fall back to default
    workspace_id = os.environ.get("TOWER_WORKSPACE_ID")
    if not workspace_id:
        # Fallback to known workspace ID if not set in ESC
        workspace_id = "59994744926013"
        print(
            f"Warning: TOWER_WORKSPACE_ID not found in ESC environment, using fallback: {workspace_id}"
        )

    return {
        "tower_access_token": os.environ.get("TOWER_ACCESS_TOKEN"),
        "tower_workspace_id": workspace_id,
        "github_token": os.environ.get("GITHUB_TOKEN"),
        # AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN)
        # are automatically handled by ESC and picked up by the AWS provider
    }
