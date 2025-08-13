"""Test IAM policy compliance against Seqera reference policy.

This test validates that our TowerForge IAM policy includes all required permissions
from the official Seqera forge policy to prevent missing permission errors.
"""

import sys
from pathlib import Path
from typing import Set, Dict, Any

import pytest
import requests

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.credentials import _create_forge_policy_document  # noqa: E402


class TestIAMPolicyCompliance:
    """Test IAM policy compliance against Seqera reference."""

    REFERENCE_POLICY_URL = "https://raw.githubusercontent.com/seqeralabs/nf-tower-aws/master/forge/forge-policy.json"

    @pytest.fixture
    def reference_policy(self) -> Dict[str, Any]:
        """Fetch the reference Seqera forge policy."""
        try:
            response = requests.get(self.REFERENCE_POLICY_URL, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            pytest.skip(f"Could not fetch reference policy: {e}")
            # This line will never be reached due to pytest.skip, but mypy needs it
            return {}

    @pytest.fixture
    def our_policy(self) -> Dict[str, Any]:
        """Get our TowerForge policy document."""
        return _create_forge_policy_document()

    def _extract_permissions_from_policy(self, policy: Dict[str, Any]) -> Set[str]:
        """Extract all Action permissions from a policy document."""
        permissions = set()

        for statement in policy.get("Statement", []):
            actions = statement.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]
            permissions.update(actions)

        return permissions

    def test_policy_includes_all_reference_permissions(
        self, reference_policy: Dict[str, Any], our_policy: Dict[str, Any]
    ):
        """Test that our policy includes all permissions from the reference policy."""
        reference_permissions = self._extract_permissions_from_policy(reference_policy)
        our_permissions = self._extract_permissions_from_policy(our_policy)

        missing_permissions = reference_permissions - our_permissions

        if missing_permissions:
            pytest.fail(
                f"Our policy is missing {len(missing_permissions)} permissions from the reference policy:\n"
                + "\n".join(f"  - {perm}" for perm in sorted(missing_permissions))
                + f"\n\nReference policy URL: {self.REFERENCE_POLICY_URL}"
            )

    def test_critical_ec2_permissions_present(self, our_policy: Dict[str, Any]):
        """Test that critical EC2 permissions are present in our policy."""
        our_permissions = self._extract_permissions_from_policy(our_policy)

        critical_ec2_permissions = {
            "ec2:DescribeAccountAttributes",
            "ec2:DescribeLaunchTemplateVersions",
            "ec2:DescribeInstanceTypeOfferings",
            "ec2:DescribeSecurityGroups",
            "ec2:DescribeSubnets",
            "ec2:DescribeLaunchTemplates",
            "ec2:DescribeKeyPairs",
            "ec2:DescribeVpcs",
            "ec2:DescribeInstanceTypes",
        }

        missing_critical = critical_ec2_permissions - our_permissions

        if missing_critical:
            pytest.fail(
                "Missing critical EC2 permissions:\n"
                + "\n".join(f"  - {perm}" for perm in sorted(missing_critical))
            )

    def test_policy_structure_is_valid(self, our_policy: Dict[str, Any]):
        """Test that our policy has valid structure."""
        assert "Version" in our_policy, "Policy must have Version field"
        assert "Statement" in our_policy, "Policy must have Statement field"
        assert isinstance(our_policy["Statement"], list), "Statement must be a list"
        assert len(our_policy["Statement"]) > 0, (
            "Policy must have at least one statement"
        )

        for i, statement in enumerate(our_policy["Statement"]):
            assert "Effect" in statement, f"Statement {i} must have Effect field"
            assert "Action" in statement, f"Statement {i} must have Action field"
            assert statement["Effect"] in ["Allow", "Deny"], (
                f"Statement {i} Effect must be Allow or Deny"
            )


# TODO: Implement Pulumi CrossGuard policy validation for automated compliance checking
# CrossGuard would allow us to enforce these policy requirements at deployment time
# and prevent non-compliant policies from being deployed.
# See: https://www.pulumi.com/docs/guides/crossguard/
