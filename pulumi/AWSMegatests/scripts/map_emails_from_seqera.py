#!/usr/bin/env python3
"""
Map GitHub usernames to emails using existing Seqera Platform workspace participants.

This script cross-references GitHub team members with current workspace participants
to find email addresses for users without public GitHub emails.
"""

import json
import os
import sys
import requests
from typing import Dict, List, Optional


def get_seqera_participants():
    """Get current participants from Seqera Platform workspace."""
    token = os.getenv("TOWER_ACCESS_TOKEN")

    if not token:
        print("Error: TOWER_ACCESS_TOKEN environment variable not set")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    workspace_id = 59994744926013  # AWSMegatests workspace
    org_id = 252464779077610  # nf-core org

    # Use official pagination parameters: max=100 (API limit) to get all participants
    url = f"https://api.cloud.seqera.io/orgs/{org_id}/workspaces/{workspace_id}/participants?max=100"

    print("Fetching ALL workspace participants...")
    print(f"URL: {url}")
    print()

    try:
        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code == 200:
            data = response.json()
            all_participants = data.get("participants", [])
            total_size = data.get("totalSize", 0)

            print(f"✓ Got {len(all_participants)}/{total_size} participants")

            if len(all_participants) < total_size:
                print(
                    "⚠️  API returned fewer participants than total, but this is the maximum per request"
                )
            else:
                print("🎉 Successfully retrieved ALL workspace participants!")

        else:
            print(f"✗ Error fetching participants: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except Exception:
                print(f"Response: {response.text}")
            return []

    except requests.exceptions.RequestException as e:
        print(f"✗ Network error: {e}")
        return []

    print(f"\n✓ Total participants found: {len(all_participants)}")
    return all_participants


def create_email_mapping(
    participants: List[Dict], github_usernames: List[str]
) -> Dict[str, Optional[str]]:
    """
    Create mapping from GitHub usernames to email addresses using Seqera participant data.

    This tries multiple matching strategies:
    1. Direct username match with participant userName
    2. Email domain matching for common patterns
    3. Fuzzy matching based on name patterns
    """
    email_mapping = {}

    print("\n=== Creating GitHub → Email Mapping ===")

    # Create lookup tables from Seqera participants
    username_to_email = {}  # userName → email
    email_patterns = {}  # pattern → email

    for participant in participants:
        username = participant.get("userName", "")
        email = participant.get("email", "")
        first_name = participant.get("firstName", "")
        last_name = participant.get("lastName", "")

        if username and email:
            username_to_email[username.lower()] = email

            # Create pattern variations
            if first_name and last_name:
                # Common GitHub username patterns
                patterns = [
                    f"{first_name.lower()}{last_name.lower()}",
                    f"{first_name.lower()}-{last_name.lower()}",
                    f"{first_name.lower()}_{last_name.lower()}",
                    f"{first_name[0].lower()}{last_name.lower()}",
                ]
                for pattern in patterns:
                    email_patterns[pattern] = email

    print(f"Found {len(username_to_email)} username→email mappings")
    print(f"Created {len(email_patterns)} pattern variations")
    print()

    # Map each GitHub username
    for github_username in github_usernames:
        github_lower = github_username.lower()

        # Strategy 1: Direct username match
        if github_lower in username_to_email:
            email = username_to_email[github_lower]
            print(f"✓ {github_username} → {email} (direct match)")
            email_mapping[github_username] = email
            continue

        # Strategy 2: Check common variations
        variations = [
            github_username.replace("-", ""),
            github_username.replace("_", ""),
            github_username.replace("-", "_"),
            github_username.replace("_", "-"),
        ]

        found = False
        for variation in variations:
            if variation.lower() in username_to_email:
                email = username_to_email[variation.lower()]
                print(f"✓ {github_username} → {email} (variation: {variation})")
                email_mapping[github_username] = email
                found = True
                break

        if found:
            continue

        # Strategy 3: Pattern matching
        if github_lower in email_patterns:
            email = email_patterns[github_lower]
            print(f"✓ {github_username} → {email} (pattern match)")
            email_mapping[github_username] = email
            continue

        # Strategy 4: Fuzzy matching based on email domains and patterns
        # Look for emails that might correspond to this GitHub user
        potential_matches = []
        for participant in participants:
            email = participant.get("email", "")
            seqera_username = participant.get("userName", "")

            if not email:
                continue

            # Direct username match with Seqera userName
            if seqera_username.lower() == github_username.lower():
                potential_matches.append(
                    (email, seqera_username, "seqera username match")
                )
            # GitHub username contains Seqera username or vice versa
            elif (
                github_username.lower() in seqera_username.lower()
                or seqera_username.lower() in github_username.lower()
            ):
                potential_matches.append(
                    (email, seqera_username, "username similarity")
                )
            # Email contains GitHub username
            elif github_username.lower() in email.lower():
                potential_matches.append(
                    (email, seqera_username, "email contains username")
                )
            # Check common variations (adamrtalbot vs adamtalbot)
            elif github_username.lower().replace("-", "") == seqera_username.lower():
                potential_matches.append(
                    (email, seqera_username, "username without dash")
                )
            # Email contains name parts
            elif any(
                part in email.lower()
                for part in github_username.lower().split("-")
                if len(part) > 2
            ):
                potential_matches.append(
                    (email, seqera_username, "email contains name parts")
                )

        if len(potential_matches) == 1:
            email, seqera_username, reason = potential_matches[0]
            print(
                f"? {github_username} → {email} (fuzzy: {reason}, seqera_user: {seqera_username})"
            )
            email_mapping[github_username] = email
        elif len(potential_matches) > 1:
            print(f"⚠️  {github_username} → Multiple potential matches:")
            for email, seqera_username, reason in potential_matches:
                print(f"     - {email} ({seqera_username}) - {reason}")
            email_mapping[github_username] = None
        else:
            print(f"✗ {github_username} → No email found")
            email_mapping[github_username] = None

    return email_mapping


def update_team_data_with_emails(email_mapping: Dict[str, Optional[str]]):
    """Update the maintainers and core team data with mapped emails."""

    # Update maintainers data
    try:
        with open("scripts/maintainers_data.json", "r") as f:
            maintainers_data = json.load(f)

        updated_count = 0
        for participant in maintainers_data["seqera_participants"]:
            github_username = participant["github_username"]

            if (
                participant["name"].startswith("github:")
                and github_username in email_mapping
            ):
                mapped_email = email_mapping[github_username]
                if mapped_email:
                    participant["name"] = mapped_email
                    participant["has_public_email"] = False  # Mapped from Seqera
                    participant["email_source"] = "seqera_workspace"
                    updated_count += 1
                    print(
                        f"Updated {github_username}: github:{github_username} → {mapped_email}"
                    )

        # Save updated maintainers data
        with open("scripts/maintainers_data.json", "w") as f:
            json.dump(maintainers_data, f, indent=2)

        print(f"\n✓ Updated {updated_count} maintainer emails from Seqera mapping")

    except Exception as e:
        print(f"Error updating maintainers data: {e}")

    # Update core team data
    try:
        with open("scripts/core_team_data.json", "r") as f:
            core_data = json.load(f)

        updated_count = 0
        for participant in core_data["seqera_participants"]:
            github_username = participant["github_username"]

            if (
                participant["name"].startswith("github:")
                and github_username in email_mapping
            ):
                mapped_email = email_mapping[github_username]
                if mapped_email:
                    participant["name"] = mapped_email
                    participant["has_public_email"] = False  # Mapped from Seqera
                    participant["email_source"] = "seqera_workspace"
                    updated_count += 1
                    print(
                        f"Updated {github_username}: github:{github_username} → {mapped_email}"
                    )

        # Save updated core team data
        with open("scripts/core_team_data.json", "w") as f:
            json.dump(core_data, f, indent=2)

        print(f"✓ Updated {updated_count} core team emails from Seqera mapping")

    except Exception as e:
        print(f"Error updating core team data: {e}")


def main():
    """Main function."""
    print("=== Email Mapping from Seqera Platform Workspace ===")
    print()

    # Get current workspace participants
    participants = get_seqera_participants()
    if not participants:
        print("No participants found")
        return

    # Load GitHub usernames that need email mapping
    github_usernames = []

    # Get usernames from maintainers without public emails
    try:
        with open("scripts/maintainers_data.json", "r") as f:
            maintainers_data = json.load(f)

        for participant in maintainers_data["seqera_participants"]:
            if participant["name"].startswith("github:"):
                github_usernames.append(participant["github_username"])
    except Exception:
        pass

    # Get usernames from core team without public emails
    try:
        with open("scripts/core_team_data.json", "r") as f:
            core_data = json.load(f)

        for participant in core_data["seqera_participants"]:
            if participant["name"].startswith("github:"):
                username = participant["github_username"]
                if username not in github_usernames:  # Avoid duplicates
                    github_usernames.append(username)
    except Exception:
        pass

    print(f"Need to map emails for {len(github_usernames)} GitHub users")

    if not github_usernames:
        print("All users already have emails!")
        return

    # Create email mapping
    email_mapping = create_email_mapping(participants, github_usernames)

    # Update team data files
    print("\n=== Updating Team Data Files ===")
    update_team_data_with_emails(email_mapping)

    # Regenerate unified data
    print("\n=== Regenerating Unified Team Data ===")
    try:
        import subprocess

        subprocess.run(
            ["uv", "run", "python", "scripts/create_unified_team_data.py"], check=True
        )
        print("✓ Unified team data regenerated")
    except Exception as e:
        print(f"Error regenerating unified data: {e}")

    # Summary
    mapped_emails = sum(1 for email in email_mapping.values() if email)
    print("\n=== Final Summary ===")
    print(f"Successfully mapped: {mapped_emails}/{len(github_usernames)} emails")
    print(f"Unmapped users: {len(github_usernames) - mapped_emails}")

    if mapped_emails > 0:
        print("\n✓ Ready to deploy with enhanced email coverage!")
    else:
        print("\n⚠️  No additional emails found in Seqera workspace")


if __name__ == "__main__":
    main()
