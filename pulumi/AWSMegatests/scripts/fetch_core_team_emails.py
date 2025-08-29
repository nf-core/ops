#!/usr/bin/env python3
"""
Script to fetch email addresses for nf-core core team members.

This script fetches core team members who should have OWNER role in the workspace.
"""

import json
import sys
from typing import Dict, List, Optional
import subprocess


def run_gh_command(command: List[str]) -> str:
    """Run a GitHub CLI command and return the output."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(command)}: {e}")
        print(f"stderr: {e.stderr}")
        sys.exit(1)


def get_core_team_members() -> List[Dict[str, str]]:
    """Fetch nf-core core team members."""
    print("Fetching nf-core core team members...")

    output = run_gh_command(
        ["gh", "api", "orgs/nf-core/teams/core/members", "--paginate"]
    )

    try:
        members = json.loads(output)
        return members
    except json.JSONDecodeError as e:
        print(f"Error parsing team members JSON: {e}")
        sys.exit(1)


def get_user_email(username: str) -> Optional[str]:
    """Get email address for a specific GitHub user."""
    try:
        output = run_gh_command(["gh", "api", f"/users/{username}", "--jq", ".email"])

        if output == "null" or not output:
            return None
        return output
    except Exception:
        return None


def main():
    """Main function to fetch core team emails."""
    members = get_core_team_members()
    print(f"Found {len(members)} core team members")

    # Extract emails
    core_team_data = []
    users_with_emails = []
    users_without_emails = []

    for member in members:
        username = member["login"]
        print(f"Checking email for {username}...", end=" ")

        email = get_user_email(username)

        member_data = {
            "username": username,
            "github_id": member["id"],
            "email": email,
            "profile_url": member["html_url"],
        }
        core_team_data.append(member_data)

        if email:
            users_with_emails.append(username)
            print(f"✓ {email}")
        else:
            users_without_emails.append(username)
            print("✗ No public email")

    # Summary
    print("\n=== Summary ===")
    print(f"Total core team members: {len(members)}")
    print(f"With public emails: {len(users_with_emails)}")
    print(f"Without public emails: {len(users_without_emails)}")

    # Output structured data
    output_data = {
        "team": "nf-core/core",
        "total_members": len(members),
        "members_with_emails": len(users_with_emails),
        "members_without_emails": len(users_without_emails),
        "core_team": core_team_data,
        "seqera_participants": [],
    }

    # Create Seqera participant entries for users with emails
    for member in core_team_data:
        if member["email"]:
            participant = {
                "name": member["email"],
                "type": "MEMBER",
                "role": "OWNER",  # Core team gets OWNER role
                "github_username": member["username"],
                "team": "core",
            }
            output_data["seqera_participants"].append(participant)

    # Save to file
    output_file = "scripts/core_team_data.json"
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\n=== Data saved to {output_file} ===")
    print(
        f"Ready to add {len(output_data['seqera_participants'])} OWNER participants to Seqera workspace"
    )

    if users_without_emails:
        print("\n=== Users without public emails ===")
        for username in users_without_emails:
            print(f"  - {username}")
        print(
            f"\nNote: These {len(users_without_emails)} users will need manual email collection"
        )

    return output_data


if __name__ == "__main__":
    main()
