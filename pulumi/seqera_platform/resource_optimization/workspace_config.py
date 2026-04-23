"""Configuration specific to the Resource Optimization workspace"""

from typing import Dict, Any


def get_workspace_config() -> Dict[str, Any]:
    """
    Get workspace-specific configuration for Resource Optimization testing.

    This workspace only includes CPU compute environments (no ARM or GPU)
    for Florian's resource optimization work.

    Returns:
        Dict containing workspace settings including compute environment configuration
    """
    return {
        "workspace_name": "ResourceOptimization",
        "organization_name": "nf-core",
        "description": "Workspace for resource optimization testing and analysis",

        # Compute environment configuration - CPU only
        "compute_environments": {
            "cpu": {
                "enabled": True,
                "name": "aws_ireland_fusionv2_nvme_cpu",
                "instance_types": ["c6id", "m6id", "r6id"],
                "max_cpus": 500,
            },
            "gpu": {
                "enabled": False,  # Not needed for resource optimization
            },
            "arm": {
                "enabled": False,  # Not needed for resource optimization
            },
        },

        # AWS configuration
        "aws_region": "eu-west-1",
        "s3_bucket_name": "nf-core-resource-optimization",

        # GitHub integration - may not be needed for this workspace
        "github_integration": {
            "enabled": False,  # Can enable later if needed
        },

        # Workspace participants - configure based on team needs
        "workspace_participants": {
            "enabled": True,
            "teams": [],  # Configure team access as needed
        },
    }
