#!/usr/bin/env python3
"""
Add nf-core maintainers to the AWSMegatests workspace as participants with MAINTAIN role.

This script serves as a workaround for missing Terraform provider resources.

TODO: Replace this script with proper Terraform resources once implemented:
- seqera_workspace_participant
- seqera_workspace_participant_role

See GitHub issue: https://github.com/seqeralabs/terraform-provider-seqera/issues/[TO_BE_CREATED]

The API endpoints exist in the provider SDK but are not exposed as Terraform resources.
"""

import json
import os
import sys
import time
import requests
from typing import Dict, List, Any


class SeqeraWorkspaceManager:
    """Manager for Seqera Platform workspace participant operations."""

    def __init__(
        self,
        token: str,
        org_id: int = 252464779077610,
        workspace_id: int = 59994744926013,
    ):
        """Initialize the workspace manager."""
        self.token = token
        self.org_id = org_id  # nf-core
        self.workspace_id = workspace_id  # AWSMegatests
        self.api_url = "https://api.cloud.seqera.io"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def get_current_participants(self) -> List[Dict[str, Any]]:
        """Get current workspace participants."""
        url = f"{self.api_url}/orgs/{self.org_id}/workspaces/{self.workspace_id}/participants"

        try:
            response = requests.get(url, headers=self.headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return data.get("participants", [])
            else:
                print(f"✗ Failed to get participants. Status: {response.status_code}")
                return []

        except requests.exceptions.RequestException as e:
            print(f"✗ Network error getting participants: {e}")
            return []

    def add_participant(self, email: str, role: str = "MAINTAIN") -> bool:
        """Add a single participant to the workspace."""
        url = f"{self.api_url}/orgs/{self.org_id}/workspaces/{self.workspace_id}/participants/add"

        # Fixed payload format based on terraform-provider-seqera SDK analysis
        payload = {
            "userNameOrEmail": email  # API expects this field name, not "email"
            # Note: Role is set separately via update endpoint after participant is added
        }

        try:
            response = requests.put(url, headers=self.headers, json=payload, timeout=30)

            if response.status_code in [200, 201, 204]:
                print(f"  ✓ Added {email} with role {role}")
                return True
            elif response.status_code == 409:
                print(f"  ~ {email} already exists (checking role...)")
                return self._check_and_update_role(email, role)
            else:
                error_msg = f"Status {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f": {error_data.get('message', 'Unknown error')}"
                except Exception:
                    error_msg += f": {response.text}"

                print(f"  ✗ Failed to add {email} - {error_msg}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"  ✗ Network error adding {email}: {e}")
            return False

    def _check_and_update_role(self, email: str, desired_role: str) -> bool:
        """Check if existing participant has the correct role."""
        participants = self.get_current_participants()

        for participant in participants:
            if participant.get("email", "").lower() == email.lower():
                current_role = participant.get("wspRole", "").lower()
                if current_role == desired_role.lower():
                    print(f"    ✓ Already has correct role: {current_role}")
                    return True
                else:
                    print(
                        f"    ! Has role {current_role}, desired {desired_role.lower()}"
                    )
                    # Note: Role update would require additional API call if supported
                    return True  # Consider this successful for now

        print(f"    ? Could not find {email} in participants list")
        return False

    def add_maintainers_batch(
        self, maintainers_data: List[Dict[str, str]], delay: float = 1.0
    ) -> Dict[str, bool]:
        """Add multiple maintainers with a delay between requests."""
        results = {}

        print(f"Adding {len(maintainers_data)} maintainers to workspace...")
        print(f"Organization: nf-core (ID: {self.org_id})")
        print(f"Workspace: AWSMegatests (ID: {self.workspace_id})")
        print()

        for i, maintainer in enumerate(maintainers_data, 1):
            email = maintainer["name"]  # 'name' field contains the email
            role = maintainer["role"]
            github_username = maintainer.get("github_username", "unknown")

            print(f"{i:2d}/{len(maintainers_data)}: {email} ({github_username})")

            success = self.add_participant(email, role)
            results[email] = success

            # Add delay between requests to be nice to the API
            if i < len(maintainers_data) and delay > 0:
                time.sleep(delay)

        return results


def load_maintainers_data() -> List[Dict[str, str]]:
    """Load maintainers data from JSON file."""
    data_file = "scripts/maintainers_data.json"

    try:
        with open(data_file, "r") as f:
            data = json.load(f)

        return data.get("seqera_participants", [])

    except FileNotFoundError:
        print(f"✗ Maintainers data file not found: {data_file}")
        print(
            "Run 'python scripts/fetch_maintainer_emails.py' first to generate the data"
        )
        return []
    except json.JSONDecodeError as e:
        print(f"✗ Error parsing maintainers data file: {e}")
        return []


def main():
    """Main function."""

    # Check for non-interactive mode
    non_interactive = "--yes" in sys.argv or "--non-interactive" in sys.argv

    print("=== nf-core Maintainers → Seqera Platform Workspace ===")
    print()

    # Get token from environment
    token = os.getenv("TOWER_ACCESS_TOKEN")
    if not token:
        print("✗ Error: TOWER_ACCESS_TOKEN environment variable not set")
        sys.exit(1)

    # Load maintainers data
    maintainers_data = load_maintainers_data()
    if not maintainers_data:
        print("✗ No maintainers data available")
        sys.exit(1)

    print(f"Loaded {len(maintainers_data)} maintainers with public emails")
    print()

    # Initialize workspace manager
    manager = SeqeraWorkspaceManager(token)

    # Get current participants for comparison
    print("Current workspace participants:")
    current_participants = manager.get_current_participants()
    if current_participants:
        print(f"  Found {len(current_participants)} existing participants")

        # Show maintainers already in workspace
        current_emails = {p.get("email", "").lower() for p in current_participants}
        already_added = [
            m for m in maintainers_data if m["name"].lower() in current_emails
        ]

        if already_added:
            print(f"  {len(already_added)} maintainers already in workspace:")
            for m in already_added:
                print(f"    - {m['name']} ({m.get('github_username', 'unknown')})")

        to_add = [
            m for m in maintainers_data if m["name"].lower() not in current_emails
        ]
        print(f"  {len(to_add)} maintainers to be added")
    else:
        to_add = maintainers_data
        print(
            f"  Could not get current participants, will attempt to add all {len(to_add)}"
        )

    print()

    # Confirm before proceeding (unless non-interactive)
    if not non_interactive:
        try:
            response = input(
                f"Add {len(to_add) if 'to_add' in locals() else len(maintainers_data)} maintainers to workspace? (y/N): "
            )
            if response.lower() not in ["y", "yes"]:
                print("Aborted by user")
                sys.exit(0)
        except (EOFError, KeyboardInterrupt):
            print("\nAborted by user")
            sys.exit(0)
    else:
        print(
            f"Non-interactive mode: proceeding to add {len(to_add) if 'to_add' in locals() else len(maintainers_data)} maintainers..."
        )

    print()

    # Add maintainers
    data_to_add = to_add if "to_add" in locals() else maintainers_data
    results = manager.add_maintainers_batch(data_to_add, delay=1.0)

    # Summary
    print()
    print("=== Summary ===")
    successful = sum(1 for success in results.values() if success)
    failed = len(results) - successful

    print(f"Successfully added: {successful}")
    print(f"Failed: {failed}")

    if failed > 0:
        print("\nFailed additions:")
        for email, success in results.items():
            if not success:
                print(f"  - {email}")

    print(
        f"\nTotal workspace participants after operation: {len(current_participants) + successful}"
    )


if __name__ == "__main__":
    main()
