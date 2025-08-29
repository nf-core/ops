#!/usr/bin/env python3
"""
Parse individual member status from Pulumi Command outputs.

This script helps analyze the workspace participant sync results.
"""

import json
import subprocess


def get_pulumi_outputs():
    """Get current Pulumi stack outputs."""
    try:
        result = subprocess.run(
            ["uv", "run", "pulumi", "stack", "output", "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Error getting Pulumi outputs: {e}")
        return {}


def parse_member_statuses(outputs):
    """Parse member sync statuses from command outputs."""
    workspace_participants = outputs.get("workspace_participants", {})
    member_commands = workspace_participants.get("individual_member_commands", {})

    print("=== Individual Team Member Sync Status ===")
    print(
        f"Total tracked members: {workspace_participants.get('total_tracked_members', 0)}"
    )
    print(f"Workspace ID: {workspace_participants.get('workspace_id', 'N/A')}")
    print("Role precedence: core team (OWNER) > maintainers (MAINTAIN)")
    print()

    statuses = {
        "ADDED": [],
        "EXISTS": [],
        "USER_NOT_FOUND": [],
        "FAILED": [],
        "UNKNOWN": [],
    }

    for username, cmd_info in member_commands.items():
        command_output = cmd_info.get("status", "")

        # Parse STATUS line from command output
        status_line = None
        for line in command_output.split("\n"):
            if line.startswith("STATUS:"):
                status_line = line
                break

        if status_line:
            # Parse: STATUS:ADDED:email@example.com:MAINTAIN
            parts = status_line.split(":")
            if len(parts) >= 4:
                status = parts[1]
                email = parts[2]
                role = parts[3]

                statuses[status].append(
                    {
                        "username": username,
                        "email": email,
                        "role": role,
                        "command_id": cmd_info.get("command_id", "N/A"),
                    }
                )
            else:
                statuses["UNKNOWN"].append(
                    {
                        "username": username,
                        "status_line": status_line,
                        "command_id": cmd_info.get("command_id", "N/A"),
                    }
                )
        else:
            statuses["UNKNOWN"].append(
                {
                    "username": username,
                    "output": command_output[:100] + "..."
                    if len(command_output) > 100
                    else command_output,
                    "command_id": cmd_info.get("command_id", "N/A"),
                }
            )

    # Display results
    for status, members in statuses.items():
        if members:
            print(f"🔸 {status}: {len(members)} members")
            for member in members:
                if status in ["ADDED", "EXISTS"]:
                    print(
                        f"  ✓ {member['username']} ({member['email']}) - {member['role']}"
                    )
                elif status == "USER_NOT_FOUND":
                    print(
                        f"  ⚠️  {member['username']} ({member['email']}) - Not in Seqera Platform"
                    )
                elif status == "FAILED":
                    print(
                        f"  ✗ {member['username']} ({member['email']}) - {member['role']}"
                    )
                else:
                    print(
                        f"  ? {member['username']} - {member.get('output', 'Unknown status')}"
                    )
            print()

    # Summary with role breakdown
    total_successful = len(statuses["ADDED"]) + len(statuses["EXISTS"])
    total_members = sum(len(members) for members in statuses.values())

    # Count by role
    role_counts = {"OWNER": 0, "MAINTAIN": 0}
    for status in ["ADDED", "EXISTS"]:
        for member in statuses[status]:
            role = member.get("role", "UNKNOWN")
            if role in role_counts:
                role_counts[role] += 1

    print("=== Summary ===")
    print(f"Successfully synced: {total_successful}/{total_members}")
    print(f"  - OWNER role: {role_counts['OWNER']} (core team)")
    print(f"  - MAINTAIN role: {role_counts['MAINTAIN']} (maintainers)")
    print(f"New additions: {len(statuses['ADDED'])}")
    print(f"Already existed: {len(statuses['EXISTS'])}")
    print(f"Failed: {len(statuses['FAILED']) + len(statuses['USER_NOT_FOUND'])}")

    return statuses


def main():
    """Main function."""
    print("=== Seqera Workspace Participant Status Parser ===")
    print()

    outputs = get_pulumi_outputs()
    if not outputs:
        print("No Pulumi outputs found")
        return

    parse_member_statuses(outputs)


if __name__ == "__main__":
    main()
