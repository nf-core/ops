"""Configuration management for iGenomes infrastructure.

This module handles loading configuration from environment variables,
specifically AWS credentials from 1Password via direnv.
"""

import os
from typing import Dict, Any


def get_configuration() -> Dict[str, Any]:
    """Load configuration from environment variables.

    Environment variables are loaded via direnv from 1Password.
    See .envrc for credential loading configuration.

    Returns:
        Dict[str, Any]: Configuration dictionary with AWS credentials and settings

    Raises:
        ValueError: If required environment variables are missing
    """
    # Load AWS credentials from environment
    aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
    aws_region = os.environ.get("AWS_DEFAULT_REGION", "eu-west-1")

    # Validate required credentials
    if not aws_access_key_id or not aws_secret_access_key:
        raise ValueError(
            "Missing AWS credentials. "
            "Ensure direnv is configured and 1Password credentials are loaded. "
            "Run 'direnv allow' in the project directory."
        )

    return {
        "aws_access_key_id": aws_access_key_id,
        "aws_secret_access_key": aws_secret_access_key,
        "aws_region": aws_region,
    }


def validate_configuration(config: Dict[str, Any]) -> None:
    """Validate configuration dictionary.

    Args:
        config: Configuration dictionary to validate

    Raises:
        ValueError: If configuration is invalid
    """
    required_keys = ["aws_access_key_id", "aws_secret_access_key", "aws_region"]

    for key in required_keys:
        if key not in config or not config[key]:
            raise ValueError(f"Missing required configuration key: {key}")
