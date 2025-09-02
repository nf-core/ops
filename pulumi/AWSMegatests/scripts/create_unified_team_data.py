#!/usr/bin/env python3
"""
Create unified team data with proper role precedence.

This script merges maintainers (MAINTAIN role) and core team (OWNER role) data,
ensuring core team members get OWNER role even if they're also in maintainers.
"""

import json


def merge_team_data():
    """Merge maintainers and core team data with proper role precedence."""

    # Load maintainers data
    try:
        with open("scripts/maintainers_data.json", "r") as f:
            maintainers_data = json.load(f)
        maintainers = maintainers_data.get("seqera_participants", [])
    except FileNotFoundError:
        print("Error: Run fetch_maintainer_emails.py first")
        return

    # Load core team data
    try:
        with open("scripts/core_team_data.json", "r") as f:
            core_data = json.load(f)
        core_members = core_data.get("seqera_participants", [])
    except FileNotFoundError:
        print("Error: Run fetch_core_team_emails.py first")
        return

    print(f"Loaded {len(maintainers)} maintainers (MAINTAIN role)")
    print(f"Loaded {len(core_members)} core team members (OWNER role)")

    # Create unified list with core team precedence
    unified_participants = {}

    # Add maintainers first (MAINTAIN role)
    for maintainer in maintainers:
        email = maintainer["name"]
        unified_participants[email] = {
            "name": email,
            "type": "MEMBER",
            "role": "MAINTAIN",
            "github_username": maintainer["github_username"],
            "teams": ["maintainers"],
            "source": "maintainers",
        }

    # Add core team members (OWNER role) - this will override maintainers
    for core_member in core_members:
        email = core_member["name"]
        if email in unified_participants:
            # Core member was also in maintainers - upgrade to OWNER
            print(
                f"🔄 {core_member['github_username']} ({email}): MAINTAIN → OWNER (core team precedence)"
            )
            unified_participants[email]["role"] = "OWNER"
            unified_participants[email]["teams"].append("core")
            unified_participants[email]["source"] = "core (upgraded from maintainers)"
        else:
            # New core member
            print(f"➕ {core_member['github_username']} ({email}): OWNER (core team)")
            unified_participants[email] = {
                "name": email,
                "type": "MEMBER",
                "role": "OWNER",
                "github_username": core_member["github_username"],
                "teams": ["core"],
                "source": "core",
            }

    # Convert back to list
    final_participants = list(unified_participants.values())

    # Create unified output
    unified_data = {
        "teams_processed": ["nf-core/maintainers", "nf-core/core"],
        "role_precedence": "core (OWNER) > maintainers (MAINTAIN)",
        "total_participants": len(final_participants),
        "role_breakdown": {
            "OWNER": len([p for p in final_participants if p["role"] == "OWNER"]),
            "MAINTAIN": len([p for p in final_participants if p["role"] == "MAINTAIN"]),
        },
        "seqera_participants": final_participants,
    }

    # Save unified data
    output_file = "scripts/unified_team_data.json"
    with open(output_file, "w") as f:
        json.dump(unified_data, f, indent=2)

    print("\n=== Unified Team Data ===")
    print(f"Total participants: {len(final_participants)}")
    print(f"OWNER role: {unified_data['role_breakdown']['OWNER']}")
    print(f"MAINTAIN role: {unified_data['role_breakdown']['MAINTAIN']}")
    print(f"Saved to: {output_file}")

    # Show role assignments
    print("\n=== Role Assignments ===")
    for role in ["OWNER", "MAINTAIN"]:
        role_members = [p for p in final_participants if p["role"] == role]
        if role_members:
            print(f"{role}: {len(role_members)} members")
            for member in role_members:
                teams_str = ", ".join(member["teams"])
                print(
                    f"  - {member['github_username']} ({member['name']}) [{teams_str}]"
                )

    return unified_data


if __name__ == "__main__":
    merge_team_data()
