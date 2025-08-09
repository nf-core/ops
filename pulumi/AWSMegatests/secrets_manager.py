"""Configuration management for AWS Megatests infrastructure using Pulumi ESC"""

import os


def get_configuration():
    """Get configuration values from ESC environment variables"""

    # All configuration comes from ESC environment variables
    # These are automatically set when the ESC environment is imported

    return {
        "tower_access_token": os.environ.get("TOWER_ACCESS_TOKEN"),
        "tower_workspace_id": "59994744926013",  # TODO: Add to ESC environment
        "github_token": os.environ.get("GITHUB_TOKEN"),
        # AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN)
        # are automatically handled by ESC and picked up by the AWS provider
    }
