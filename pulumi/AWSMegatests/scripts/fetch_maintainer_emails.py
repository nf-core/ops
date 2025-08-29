#!/usr/bin/env python3
"""
Script to fetch email addresses for nf-core maintainers team members.

This script:
1. Fetches GitHub team members from nf-core/maintainers
2. Extracts public email addresses where available
3. Provides a structured output for Seqera Platform workspace participant management

Usage:
    python scripts/fetch_maintainer_emails.py

Environment Variables:
    GITHUB_TOKEN: GitHub personal access token with org:read permissions
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


def get_team_members() -> List[Dict[str, str]]:
    """Fetch nf-core maintainers team members."""
    print("Fetching nf-core maintainers team members...")

    # Get team members
    output = run_gh_command(
        ["gh", "api", "orgs/nf-core/teams/maintainers/members", "--paginate"]
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

        # gh returns 'null' as string when email is None
        if output == "null" or not output:
            return None
        return output
    except Exception:
        return None


def main():
    """Main function to fetch maintainer emails."""
    # Check if GitHub CLI is available
    try:
        subprocess.run(["gh", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: GitHub CLI (gh) is required but not found.")
        print("Please install it: https://cli.github.com/")
        sys.exit(1)

    # Get team members
    members = get_team_members()
    print(f"Found {len(members)} team members")

    # Extract emails
    maintainers_data = []
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
        maintainers_data.append(member_data)

        if email:
            users_with_emails.append(username)
            print(f"✓ {email}")
        else:
            users_without_emails.append(username)
            print("✗ No public email")

    # Summary
    print("\n=== Summary ===")
    print(f"Total maintainers: {len(members)}")
    print(f"With public emails: {len(users_with_emails)}")
    print(f"Without public emails: {len(users_without_emails)}")

    # Output structured data
    output_data = {
        "team": "nf-core/maintainers",
        "total_members": len(members),
        "members_with_emails": len(users_with_emails),
        "members_without_emails": len(users_without_emails),
        "maintainers": maintainers_data,
        "seqera_participants": [],
    }

    # Create Seqera participant entries for users with emails
    for member in maintainers_data:
        if member["email"]:
            participant = {
                "name": member["email"],
                "type": "MEMBER",
                "role": "MAINTAIN",
                "github_username": member["username"],
            }
            output_data["seqera_participants"].append(participant)

    # Save to file
    output_file = "scripts/maintainers_data.json"
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\n=== Data saved to {output_file} ===")
    print(
        f"Ready to add {len(output_data['seqera_participants'])} participants to Seqera workspace"
    )

    if users_without_emails:
        print("\n=== Users without public emails ===")
        for username in users_without_emails:
            print(f"  - {username}")
        print(
            f"\nNote: These {len(users_without_emails)} users will need manual email collection"
        )
        print("or can be added later once their emails are obtained.")

    return output_data


if __name__ == "__main__":
    main()
