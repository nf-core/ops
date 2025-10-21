"""Configuration specific to the AWS Megatests workspace"""

from typing import Dict, Any


def get_workspace_config() -> Dict[str, Any]:
    """
    Get workspace-specific configuration for AWS Megatests.

    Returns:
        Dict containing workspace settings including compute environment configuration
    """
    return {
        "workspace_name": "AWSmegatests",
        "organization_name": "nf-core",
        "description": "Workspace for nf-core AWS megatests infrastructure",

        # Compute environment configuration
        "compute_environments": {
            "cpu": {
                "enabled": True,
                "name": "aws_ireland_fusionv2_nvme_cpu",
                "instance_types": ["c6id", "m6id", "r6id"],
                "max_cpus": 500,
            },
            "gpu": {
                "enabled": True,
                "name": "aws_ireland_fusionv2_nvme_gpu",
                "instance_types": ["g4dn", "g5"],
                "max_cpus": 500,
            },
            "arm": {
                "enabled": True,
                "name": "aws_ireland_fusionv2_nvme_arm",
                "instance_types": ["c6gd", "m6gd", "r6gd"],
                "max_cpus": 500,
            },
        },

        # AWS configuration
        "aws_region": "eu-west-1",
        "s3_bucket_name": "nf-core-awsmegatests",

        # GitHub integration
        "github_integration": {
            "enabled": True,
            "organization": "nf-core",
        },

        # Workspace participants
        "workspace_participants": {
            "enabled": True,
            "teams": ["nf-core", "nf-core-maintainers"],
        },
    }
