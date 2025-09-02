"""Seqera Platform workspace participant management using Pulumi Command provider."""

import json
import pulumi
import pulumi_command as command
from typing import Dict, List, Optional
from ..utils.logging import log_info


def create_team_data_setup_command(
    workspace_id: int,
    seqera_token: str,
    github_token: str,
    opts: Optional[pulumi.ResourceOptions] = None,
) -> command.local.Command:
    """
    Create a Pulumi Command that generates team data with proper credentials.

    This runs the team data setup scripts automatically during Pulumi deployment.
    """
    setup_cmd = command.local.Command(
        "team-data-setup",
        create="""
# Generate team member data with proper credentials
echo "=== Setting up team member data with privacy protection ==="

# Run setup script with environment credentials
uv run python scripts/setup_team_data.py

echo "✓ Team data setup completed"
echo "Files generated locally (not committed to git):"
echo "  - scripts/maintainers_data.json" 
echo "  - scripts/core_team_data.json"
echo "  - scripts/unified_team_data.json"
        """,
        environment={
            "GITHUB_TOKEN": github_token,
            "TOWER_ACCESS_TOKEN": seqera_token,
        },
        opts=opts,
    )

    return setup_cmd


def create_individual_member_commands(
    workspace_id: int,
    token: str,
    github_token: str,
    org_id: int = 252464779077610,  # nf-core
    opts: Optional[pulumi.ResourceOptions] = None,
) -> tuple[command.local.Command, Dict[str, command.local.Command]]:
    """
    Create individual Pulumi Command resources for each GitHub team member.

    This provides granular tracking of each maintainer's workspace participant status.
    """
    # First, ensure team data is set up with proper credentials
    setup_cmd = create_team_data_setup_command(workspace_id, token, github_token, opts)

    # Generate team data at runtime to avoid committing private emails
    log_info("Team data will be generated automatically during deployment...")

    # Load team data (will be available after setup command runs)
    try:
        with open("scripts/unified_team_data.json", "r") as f:
            data = json.load(f)
        team_members = data.get("seqera_participants", [])
        log_info(f"Loaded {len(team_members)} team members from runtime data")
    except FileNotFoundError:
        # For preview purposes, show expected team count
        log_info("Team data will be generated during deployment (35 expected members)")
        team_members = []
    except Exception as e:
        log_info(f"Team data will be generated at runtime: {e}")
        team_members = []

    member_commands = {}

    log_info(f"Creating individual tracking for {len(team_members)} team members")

    for member in team_members:
        email = member["name"]
        github_username = member["github_username"]
        role = member["role"]  # OWNER for core team, MAINTAIN for maintainers

        # Create safe resource name
        safe_name = github_username.replace("-", "_").replace(".", "_")

        # Note: Role precedence handled in bash script (core team checked first)

        # Create individual command for this member
        member_cmd = command.local.Command(
            f"team_sync_{safe_name}",
            create=f'''
#!/bin/bash
# Sync GitHub team member '{github_username}' to Seqera workspace with {role} role
echo "=== Syncing {github_username} ({email}) as {role} ==="

# Verify user is still in appropriate GitHub teams
echo "Checking GitHub team membership..."
found_in_team=false

# Check core team first (higher precedence)
if gh api orgs/nf-core/teams/core/members --jq '.[].login' | grep -q "^{github_username}$"; then
    echo "✓ {github_username} confirmed in nf-core/core team (OWNER role)"
    current_role="OWNER"
    found_in_team=true
elif gh api orgs/nf-core/teams/maintainers/members --jq '.[].login' | grep -q "^{github_username}$"; then
    echo "✓ {github_username} confirmed in nf-core/maintainers team (MAINTAIN role)"
    current_role="MAINTAIN"
    found_in_team=true
fi

if [ "$found_in_team" = false ]; then
    echo "⚠️  {github_username} not found in any relevant team, skipping"
    exit 0
fi

# Ensure we're using the correct role (core team precedence)
target_role="{role}"
if [ "$current_role" != "$target_role" ]; then
    echo "🔄 Role precedence: Using $current_role (detected) instead of $target_role"
    target_role="$current_role"
fi

# Check current email (in case it changed)
echo "Fetching current email..."
current_email=$(gh api /users/{github_username} --jq '.email // empty')

# Handle members without public emails
if [[ "{email}" == github:* ]]; then
    # Member has no public email, try to get current one
    if [ -z "$current_email" ]; then
        echo "⚠️  {github_username} has no public email - cannot add to Seqera Platform"
        echo "STATUS:NO_EMAIL:{github_username}:$target_role"
        exit 0
    else
        echo "✓ {github_username} now has public email: $current_email" 
    fi
else
    # Member had cached email, check if it changed
    cached_email="{email}"
    if [ -z "$current_email" ]; then
        echo "⚠️  {github_username} email no longer public, using cached: $cached_email"
        current_email="$cached_email"
    elif [ "$current_email" != "$cached_email" ]; then
        echo "🔄 {github_username} email changed: $cached_email → $current_email"
    else
        echo "✓ Current email confirmed: $current_email"
    fi
fi

# Add to Seqera workspace
echo "Adding to Seqera workspace {workspace_id}..."
response=$(curl -s -w "%{{http_code}}" -X PUT \\
    "https://api.cloud.seqera.io/orgs/{org_id}/workspaces/{workspace_id}/participants/add" \\
    -H "Authorization: Bearer {token}" \\
    -H "Content-Type: application/json" \\
    -d '{{"userNameOrEmail": "'$current_email'"}}')

http_code="${{response: -3}}"
response_body="${{response%???}}"

case $http_code in
    200|201|204)
        echo "✓ Successfully added {github_username} with $target_role role"
        echo "STATUS:ADDED:$current_email:$target_role"
        ;;
    409)
        echo "~ {github_username} already exists in workspace"
        echo "STATUS:EXISTS:$current_email:$target_role"
        ;;
    404)
        echo "✗ User not found in Seqera Platform: $current_email"
        echo "STATUS:USER_NOT_FOUND:$current_email:N/A"
        ;;
    *)
        echo "✗ Failed to add {github_username}: HTTP $http_code"
        echo "Response: $response_body"
        echo "STATUS:FAILED:$current_email:ERROR"
        exit 1
        ;;
esac

echo "Completed sync for {github_username}"
            ''',
            environment={
                "GITHUB_TOKEN": github_token,
            },
            opts=pulumi.ResourceOptions(
                depends_on=[setup_cmd],
                parent=opts.parent if opts else None,
            ),
        )

        member_commands[github_username] = member_cmd

    return setup_cmd, member_commands


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
