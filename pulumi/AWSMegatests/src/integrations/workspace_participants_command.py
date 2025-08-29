"""Seqera Platform workspace participant management using Pulumi Command provider."""

import pulumi
import pulumi_command as command
from typing import Dict, List, Optional
from ..utils.logging import log_info


def create_workspace_participants_via_command(
    workspace_id: int,
    token: str,
    participants_data: List[Dict[str, str]],
    opts: Optional[pulumi.ResourceOptions] = None,
) -> command.local.Command:
    """
    Create workspace participants using Pulumi Command provider to run the Python script.

    Args:
        workspace_id: Seqera workspace ID
        token: Seqera API access token
        participants_data: List of participant dictionaries
        opts: Pulumi resource options

    Returns:
        Command resource that manages workspace participants
    """
    # Create the command that will run our Python script
    participant_count = len(participants_data)
    log_info(f"Creating command to add {participant_count} workspace participants")

    # The command runs within the Pulumi execution context
    add_participants_cmd = command.local.Command(
        "add-workspace-participants",
        create="uv run python scripts/add_maintainers_to_workspace.py --yes",
        environment={
            "TOWER_ACCESS_TOKEN": token,
            "TOWER_WORKSPACE_ID": str(workspace_id),
        },
        opts=pulumi.ResourceOptions(**opts.__dict__ if opts else {}),
    )

    return add_participants_cmd


def create_workspace_participants_verification(
    workspace_id: int,
    token: str,
    depends_on: List[pulumi.Resource],
    opts: Optional[pulumi.ResourceOptions] = None,
) -> command.local.Command:
    """
    Create a verification command that checks workspace participants were added correctly.

    Args:
        workspace_id: Seqera workspace ID
        token: Seqera API access token
        depends_on: Resources this command depends on
        opts: Pulumi resource options

    Returns:
        Command resource that verifies workspace participants
    """
    verification_cmd = command.local.Command(
        "verify-workspace-participants",
        create="uv run python scripts/inspect_participants.py",
        environment={
            "TOWER_ACCESS_TOKEN": token,
            "TOWER_WORKSPACE_ID": str(workspace_id),
        },
        opts=pulumi.ResourceOptions(
            depends_on=depends_on, **(opts.__dict__ if opts else {})
        ),
    )

    return verification_cmd
