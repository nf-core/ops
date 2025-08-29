#!/usr/bin/env python3
"""
Setup script to generate team data locally without committing private emails.

This script generates the team member data files that are needed for Pulumi deployment
but excludes them from git to protect private email addresses.

Usage:
    uv run python scripts/setup_team_data.py

Environment Requirements:
    GITHUB_TOKEN: GitHub token with org:read permissions
    TOWER_ACCESS_TOKEN: Seqera Platform token with workspace access
"""

import subprocess
import sys
import os


def run_script(script_path: str, description: str):
    """Run a script and handle errors."""
    print(f"=== {description} ===")
    print(f"Running: {script_path}")

    try:
        result = subprocess.run(
            ["uv", "run", "python", script_path],
            check=True,
            capture_output=True,
            text=True,
        )
        print(f"✓ {description} completed")
        if result.stdout:
            # Show last few lines of output
            lines = result.stdout.strip().split("\n")
            for line in lines[-3:]:
                if line.strip():
                    print(f"  {line}")
        print()
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed")
        print(f"Error: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        print()
        return False


def check_environment():
    """Check required environment variables."""
    print("=== Environment Check ===")

    required_vars = ["GITHUB_TOKEN", "TOWER_ACCESS_TOKEN"]
    missing_vars = []

    for var in required_vars:
        if os.getenv(var):
            print(f"✓ {var} is set")
        else:
            print(f"✗ {var} is missing")
            missing_vars.append(var)

    if missing_vars:
        print(f"\nError: Missing environment variables: {missing_vars}")
        print("Please set them before running this script:")
        print("  GITHUB_TOKEN: GitHub token with org:read permissions")
        print("  TOWER_ACCESS_TOKEN: Seqera Platform token")
        return False

    print("✓ All environment variables present")
    print()
    return True


def main():
    """Main setup function."""
    print("=== Team Data Setup (Private Email Safe) ===")
    print()
    print("This script generates team member data locally without committing")
    print("private email addresses to git history.")
    print()

    # Check environment
    if not check_environment():
        sys.exit(1)

    # Run setup scripts in order
    scripts = [
        ("scripts/fetch_maintainer_emails.py", "Fetch maintainers team emails"),
        ("scripts/fetch_core_team_emails.py", "Fetch core team emails"),
        ("scripts/map_emails_from_seqera.py", "Map emails from Seqera workspace"),
    ]

    all_success = True

    for script_path, description in scripts:
        success = run_script(script_path, description)
        if not success:
            all_success = False
            break

    if all_success:
        print("🎉 Team data setup completed successfully!")
        print()
        print("Generated files (not committed to git):")
        print("  - scripts/maintainers_data.json")
        print("  - scripts/core_team_data.json")
        print("  - scripts/unified_team_data.json")
        print()
        print("✅ Ready for Pulumi deployment:")
        print("    uv run pulumi up --yes")
        print()
        print("📊 To view team member status after deployment:")
        print("    uv run python scripts/parse_member_status.py")
    else:
        print("⚠️  Team data setup failed")
        print("Please check the errors above and try again")
        sys.exit(1)


if __name__ == "__main__":
    main()
