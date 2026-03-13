"""Simple workspace participant management using Pulumi's apply() pattern."""

import json
import pulumi
import requests
from typing import Dict, List, Any
from utils.logging import log_info


def add_workspace_participant_simple(
    email: str,
    role: str,
    workspace_id: pulumi.Output[str],
    token: pulumi.Output[str],
    org_id: int = 252464779077610,
) -> pulumi.Output[Dict[str, Any]]:
    """
    Add a workspace participant using Pulumi's apply() pattern.

    This is simpler than dynamic resources but still integrates with Pulumi.
    """

    def _add_participant(args):
        """Internal function that does the actual API call."""
        workspace_id_val, token_val = args

        headers = {
            "Authorization": f"Bearer {token_val}",
            "Content-Type": "application/json",
        }

        url = f"https://api.cloud.seqera.io/orgs/{org_id}/workspaces/{workspace_id_val}/participants/add"
        payload = {"userNameOrEmail": email}

        try:
            response = requests.put(url, headers=headers, json=payload, timeout=30)

            if response.status_code in [200, 201, 204]:
                return {
                    "email": email,
                    "role": role,
                    "workspace_id": workspace_id_val,
                    "status": "added",
                    "participant_id": f"{org_id}:{workspace_id_val}:{email}",
                }
            elif response.status_code == 409:
                return {
                    "email": email,
                    "role": role,
                    "workspace_id": workspace_id_val,
                    "status": "already_exists",
                    "participant_id": f"{org_id}:{workspace_id_val}:{email}",
                }
            else:
                return {
                    "email": email,
                    "role": role,
                    "workspace_id": workspace_id_val,
                    "status": "failed",
                    "error": f"HTTP {response.status_code}",
                }

        except Exception as e:
            return {
                "email": email,
                "role": role,
                "workspace_id": workspace_id_val,
                "status": "error",
                "error": str(e),
            }

    # Use Pulumi's apply to handle the async nature of Outputs
    return pulumi.Output.all(workspace_id, token).apply(_add_participant)


def create_workspace_participants_simple(
    workspace_id: pulumi.Output[str],
    token: pulumi.Output[str],
    maintainer_emails: List[str],
    role: str = "MAINTAIN",
) -> pulumi.Output[List[Dict[str, Any]]]:
    """
    Create multiple workspace participants using the simple approach.

    Args:
        workspace_id: Seqera workspace ID as Pulumi Output
        token: Seqera API token as Pulumi Output
        maintainer_emails: List of email addresses to add
        role: Role to assign (default: MAINTAIN)

    Returns:
        Pulumi Output containing list of participant creation results
    """

    participant_outputs = []

    for email in maintainer_emails:
        participant_result = add_workspace_participant_simple(
            email, role, workspace_id, token
        )
        participant_outputs.append(participant_result)

    # Combine all outputs into a single list
    return pulumi.Output.all(*participant_outputs)


def load_maintainer_emails_static() -> List[str]:
    """Load maintainer emails from the JSON file (static version for Pulumi)."""
    try:
        with open("scripts/maintainers_data.json", "r") as f:
            data = json.load(f)

        participants = data.get("seqera_participants", [])
        emails = [p["name"] for p in participants]

        log_info(f"Loaded {len(emails)} maintainer emails for workspace participants")
        return emails

    except FileNotFoundError:
        log_info("Maintainers data file not found, skipping workspace participants")
        return []
    except Exception as e:
        log_info(f"Error loading maintainers data: {e}")
        return []
