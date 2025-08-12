"""Seqera provider configuration for AWS Megatests infrastructure."""

import pulumi
import pulumi_seqera as seqera
from typing import Dict, Any
from ..utils.constants import SEQERA_API_URL, ERROR_MESSAGES


class SeqeraProviderError(Exception):
    """Exception raised when Seqera provider initialization fails."""

    pass


def create_seqera_provider(config: Dict[str, Any]) -> seqera.Provider:
    """Create and configure the Seqera provider with error handling.

    Args:
        config: Configuration dictionary containing tower_access_token

    Returns:
        seqera.Provider: Configured Seqera provider instance

    Raises:
        SeqeraProviderError: If provider creation fails
        ValueError: If required configuration is missing
    """
    # Validate required configuration
    if not config.get("tower_access_token"):
        raise ValueError(ERROR_MESSAGES["missing_tower_token"])

    pulumi.log.info("Creating Seqera provider with Cloud API endpoint")

    return seqera.Provider(
        "seqera-provider",
        bearer_auth=config["tower_access_token"],
        server_url=SEQERA_API_URL,
    )
