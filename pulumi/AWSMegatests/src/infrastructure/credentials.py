"""TowerForge IAM credentials management module.

This module creates and manages IAM resources for TowerForge AWS operations,
including policies for Forge operations, Launch operations, and S3 bucket access.
It also uploads the credentials to Seqera Platform for use by compute environments.
"""

import json
from typing import Optional, Tuple, Dict, Any

import pulumi
import pulumi_aws as aws
import pulumi_seqera as seqera

from ..utils.constants import (
    TOWERFORGE_USER_NAME,
    TOWERFORGE_POLICY_NAMES,
    TOWERFORGE_CREDENTIAL_NAME,
    TOWERFORGE_CREDENTIAL_DESCRIPTION,
    TIMEOUTS,
)


class CredentialError(Exception):
    """Exception raised when credential operations fail."""

    pass


def _create_forge_policy_document() -> Dict[str, Any]:
    """Create TowerForge Forge Policy document with comprehensive permissions."""
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "TowerForge0",
                "Effect": "Allow",
                "Action": [
                    "ssm:GetParameters",
                    "iam:CreateInstanceProfile",
                    "iam:DeleteInstanceProfile",
                    "iam:AddRoleToInstanceProfile",
                    "iam:RemoveRoleFromInstanceProfile",
                    "iam:CreateRole",
                    "iam:DeleteRole",
                    "iam:AttachRolePolicy",
                    "iam:DetachRolePolicy",
                    "iam:PutRolePolicy",
                    "iam:DeleteRolePolicy",
                    "iam:PassRole",
                    "iam:TagRole",
                    "iam:TagInstanceProfile",
                    "iam:ListRolePolicies",
                    "iam:ListAttachedRolePolicies",
                    "iam:GetRole",
                    "batch:CreateComputeEnvironment",
                    "batch:UpdateComputeEnvironment",
                    "batch:DeleteComputeEnvironment",
                    "batch:CreateJobQueue",
                    "batch:UpdateJobQueue",
                    "batch:DeleteJobQueue",
                    "batch:DescribeComputeEnvironments",
                    "batch:DescribeJobQueues",
                    "fsx:CreateFileSystem",
                    "fsx:DeleteFileSystem",
                    "fsx:DescribeFileSystems",
                    "fsx:TagResource",
                    "ec2:DescribeSecurityGroups",
                    "ec2:DescribeAccountAttributes",
                    "ec2:DescribeSubnets",
                    "ec2:DescribeLaunchTemplates",
                    "ec2:DescribeLaunchTemplateVersions",
                    "ec2:CreateLaunchTemplate",
                    "ec2:DeleteLaunchTemplate",
                    "ec2:DescribeKeyPairs",
                    "ec2:DescribeVpcs",
                    "ec2:DescribeInstanceTypes",
                    "ec2:DescribeInstanceTypeOfferings",
                    "ec2:GetEbsEncryptionByDefault",
                    "efs:CreateFileSystem",
                    "efs:DeleteFileSystem",
                    "efs:DescribeFileSystems",
                    "efs:CreateMountTarget",
                    "efs:DeleteMountTarget",
                    "efs:DescribeMountTargets",
                    "efs:ModifyFileSystem",
                    "efs:PutLifecycleConfiguration",
                    "efs:TagResource",
                    "elasticfilesystem:CreateFileSystem",
                    "elasticfilesystem:DeleteFileSystem",
                    "elasticfilesystem:DescribeFileSystems",
                    "elasticfilesystem:CreateMountTarget",
                    "elasticfilesystem:DeleteMountTarget",
                    "elasticfilesystem:DescribeMountTargets",
                    "elasticfilesystem:UpdateFileSystem",
                    "elasticfilesystem:PutLifecycleConfiguration",
                    "elasticfilesystem:TagResource",
                ],
                "Resource": "*",
            },
            {
                "Sid": "TowerLaunch0",
                "Effect": "Allow",
                "Action": [
                    "s3:Get*",
                    "s3:List*",
                    "batch:DescribeJobQueues",
                    "batch:CancelJob",
                    "batch:SubmitJob",
                    "batch:ListJobs",
                    "batch:TagResource",
                    "batch:DescribeComputeEnvironments",
                    "batch:TerminateJob",
                    "batch:DescribeJobs",
                    "batch:RegisterJobDefinition",
                    "batch:DescribeJobDefinitions",
                    "ecs:DescribeTasks",
                    "ec2:DescribeInstances",
                    "ec2:DescribeInstanceTypes",
                    "ec2:DescribeInstanceAttribute",
                    "ecs:DescribeContainerInstances",
                    "ec2:DescribeInstanceStatus",
                    "ec2:DescribeImages",
                    "logs:Describe*",
                    "logs:Get*",
                    "logs:List*",
                    "logs:StartQuery",
                    "logs:StopQuery",
                    "logs:TestMetricFilter",
                    "logs:FilterLogEvents",
                    "ses:SendRawEmail",
                    "secretsmanager:ListSecrets",
                ],
                "Resource": "*",
            },
        ],
    }


def _create_launch_policy_document() -> Dict[str, Any]:
    """Create TowerForge Launch Policy document with limited permissions."""
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "TowerLaunch0",
                "Effect": "Allow",
                "Action": [
                    "batch:DescribeJobQueues",
                    "batch:CancelJob",
                    "batch:SubmitJob",
                    "batch:ListJobs",
                    "batch:TagResource",
                    "batch:DescribeComputeEnvironments",
                    "batch:TerminateJob",
                    "batch:DescribeJobs",
                    "batch:RegisterJobDefinition",
                    "batch:DescribeJobDefinitions",
                    "ecs:DescribeTasks",
                    "ec2:DescribeInstances",
                    "ec2:DescribeInstanceTypes",
                    "ec2:DescribeInstanceAttribute",
                    "ecs:DescribeContainerInstances",
                    "ec2:DescribeInstanceStatus",
                    "ec2:DescribeImages",
                    "logs:Describe*",
                    "logs:Get*",
                    "logs:List*",
                    "logs:StartQuery",
                    "logs:StopQuery",
                    "logs:TestMetricFilter",
                    "logs:FilterLogEvents",
                    "ses:SendRawEmail",
                    "secretsmanager:ListSecrets",
                ],
                "Resource": "*",
            }
        ],
    }


def _create_s3_policy_document(bucket_arn: str) -> Dict[str, Any]:
    """Create S3 bucket access policy document.

    Args:
        bucket_arn: ARN of the S3 bucket to grant access to

    Returns:
        Dict[str, Any]: S3 policy document
    """
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["s3:ListBucket"],
                "Resource": [bucket_arn],
            },
            {
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:PutObjectTagging",
                    "s3:DeleteObject",
                ],
                "Resource": [f"{bucket_arn}/*"],
                "Effect": "Allow",
            },
        ],
    }


def create_seqera_credentials(
    seqera_provider: seqera.Provider,
    workspace_id: float,
    access_key_id: pulumi.Output[str],
    access_key_secret: pulumi.Output[str],
) -> seqera.Credential:
    """Upload TowerForge AWS credentials to Seqera Platform.

    Args:
        seqera_provider: Configured Seqera provider instance
        workspace_id: Seqera Platform workspace ID
        access_key_id: AWS access key ID from TowerForge IAM user
        access_key_secret: AWS secret access key from TowerForge IAM user

    Returns:
        seqera.Credential: Seqera credential resource with credentials_id

    Raises:
        CredentialError: If credential upload fails
    """
    pulumi.log.info("Uploading TowerForge credentials to Seqera Platform")

    # Create AWS credentials configuration for Seqera Platform
    aws_keys = seqera.CredentialKeysArgs(
        aws=seqera.CredentialKeysAwsArgs(
            access_key=access_key_id,
            secret_key=access_key_secret,
            # Note: assume_role_arn is optional and not needed for direct IAM user credentials
        )
    )

    # Upload credentials to Seqera Platform
    seqera_credential = seqera.Credential(
        "towerforge-aws-credential",
        name=TOWERFORGE_CREDENTIAL_NAME,
        description=TOWERFORGE_CREDENTIAL_DESCRIPTION,
        provider_type="aws",
        workspace_id=workspace_id,
        keys=aws_keys,
        opts=pulumi.ResourceOptions(
            provider=seqera_provider,
            # Ensure credentials are uploaded after IAM access key is created
            custom_timeouts=pulumi.CustomTimeouts(
                create=TIMEOUTS["seqera_credential_create"],
                update=TIMEOUTS["seqera_credential_update"],
                delete=TIMEOUTS["seqera_credential_delete"],
            ),
        ),
    )

    return seqera_credential


def _create_iam_policies(
    aws_provider: aws.Provider, s3_bucket
) -> Tuple[aws.iam.Policy, aws.iam.Policy, aws.iam.Policy]:
    """Create IAM policies for TowerForge operations.

    Args:
        aws_provider: Configured AWS provider instance
        s3_bucket: S3 bucket resource for policy attachment

    Returns:
        Tuple of (forge_policy, launch_policy, s3_policy)
    """
    # TowerForge Forge Policy - Comprehensive permissions for resource creation
    forge_policy = aws.iam.Policy(
        "towerforge-forge-policy",
        name=TOWERFORGE_POLICY_NAMES["forge"],
        description="IAM policy for TowerForge to create and manage AWS Batch resources",
        policy=json.dumps(_create_forge_policy_document()),
        opts=pulumi.ResourceOptions(provider=aws_provider),
    )

    # TowerForge Launch Policy - Limited permissions for pipeline execution
    launch_policy = aws.iam.Policy(
        "towerforge-launch-policy",
        name=TOWERFORGE_POLICY_NAMES["launch"],
        description="IAM policy for TowerForge to launch and monitor pipeline executions",
        policy=json.dumps(_create_launch_policy_document()),
        opts=pulumi.ResourceOptions(provider=aws_provider),
    )

    # TowerForge S3 Bucket Access Policy - Access to specified S3 bucket
    s3_policy = aws.iam.Policy(
        "towerforge-s3-policy",
        name=TOWERFORGE_POLICY_NAMES["s3"],
        description=s3_bucket.bucket.apply(
            lambda bucket_name: f"IAM policy for TowerForge to access {bucket_name} S3 bucket"
        ),
        policy=s3_bucket.arn.apply(
            lambda arn: json.dumps(_create_s3_policy_document(arn))
        ),
        opts=pulumi.ResourceOptions(provider=aws_provider, depends_on=[s3_bucket]),
    )

    return forge_policy, launch_policy, s3_policy


def create_towerforge_credentials(
    aws_provider: aws.Provider,
    s3_bucket,
    seqera_provider: seqera.Provider,
    workspace_id: float,
) -> Tuple[pulumi.Output[str], pulumi.Output[str], pulumi.Output[str]]:
    """Create TowerForge IAM resources and upload to Seqera Platform.

    Creates IAM policies, user, and access keys for TowerForge operations,
    then uploads the credentials to Seqera Platform for use by compute environments.
    Based on https://github.com/seqeralabs/nf-tower-aws

    Args:
        aws_provider: Configured AWS provider instance
        s3_bucket: S3 bucket resource for policy attachment
        seqera_provider: Configured Seqera provider instance
        workspace_id: Seqera Platform workspace ID

    Returns:
        Tuple: (access_key_id, access_key_secret, seqera_credentials_id)
    """
    # Create IAM policies
    forge_policy, launch_policy, s3_policy = _create_iam_policies(
        aws_provider, s3_bucket
    )

    # Create TowerForge IAM User
    towerforge_user = aws.iam.User(
        "towerforge-user",
        name=TOWERFORGE_USER_NAME,
        opts=pulumi.ResourceOptions(provider=aws_provider),
    )

    # Attach policies to the TowerForge user
    forge_attachment = aws.iam.UserPolicyAttachment(
        "towerforge-forge-policy-attachment",
        user=towerforge_user.name,
        policy_arn=forge_policy.arn,
        opts=pulumi.ResourceOptions(
            provider=aws_provider, depends_on=[towerforge_user, forge_policy]
        ),
    )

    launch_attachment = aws.iam.UserPolicyAttachment(
        "towerforge-launch-policy-attachment",
        user=towerforge_user.name,
        policy_arn=launch_policy.arn,
        opts=pulumi.ResourceOptions(
            provider=aws_provider,
            depends_on=[towerforge_user, launch_policy],
        ),
    )

    s3_attachment = aws.iam.UserPolicyAttachment(
        "towerforge-s3-policy-attachment",
        user=towerforge_user.name,
        policy_arn=s3_policy.arn,
        opts=pulumi.ResourceOptions(
            provider=aws_provider, depends_on=[towerforge_user, s3_policy]
        ),
    )

    # Create access keys for the TowerForge user
    towerforge_access_key = aws.iam.AccessKey(
        "towerforge-access-key",
        user=towerforge_user.name,
        opts=pulumi.ResourceOptions(
            provider=aws_provider,
            depends_on=[forge_attachment, launch_attachment, s3_attachment],
            additional_secret_outputs=["secret"],
        ),
    )

    # Upload the credentials to Seqera Platform
    seqera_credential = create_seqera_credentials(
        seqera_provider=seqera_provider,
        workspace_id=workspace_id,
        access_key_id=towerforge_access_key.id,
        access_key_secret=towerforge_access_key.secret,
    )

    # Return the access key credentials and Seqera credentials ID
    return (
        towerforge_access_key.id,
        towerforge_access_key.secret,
        seqera_credential.credentials_id,
    )


def get_towerforge_resources(
    aws_provider: aws.Provider,
    s3_bucket,
    seqera_provider: Optional[seqera.Provider] = None,
    workspace_id: Optional[float] = None,
) -> Dict[str, Any]:
    """Create TowerForge resources and return resource information for exports.

    This function creates the TowerForge IAM resources and returns a dictionary
    containing resource information for Pulumi exports.

    Args:
        aws_provider: Configured AWS provider instance
        s3_bucket: S3 bucket resource for policy attachment
        seqera_provider: Optional Seqera provider for credential upload
        workspace_id: Optional workspace ID for Seqera Platform

    Returns:
        Dict[str, Any]: Resource information for Pulumi exports

    Raises:
        ValueError: If required parameters are missing
    """
    # Create the credentials (this will create all the resources)
    if seqera_provider and workspace_id:
        access_key_id, access_key_secret, seqera_credentials_id = (
            create_towerforge_credentials(
                aws_provider, s3_bucket, seqera_provider, workspace_id
            )
        )
    else:
        # Fallback for backward compatibility - this will raise an error since signature changed
        raise ValueError(
            "get_towerforge_resources now requires seqera_provider and workspace_id parameters. "
            "Please update your code to use the new signature or call create_towerforge_credentials directly."
        )

    return {
        "user": {
            "name": TOWERFORGE_USER_NAME,
            "arn": f"arn:aws:iam::{{aws_account_id}}:user/{TOWERFORGE_USER_NAME}",  # Will be populated by Pulumi
        },
        "access_key_id": access_key_id,
        "access_key_secret": access_key_secret,
        "seqera_credentials_id": seqera_credentials_id,
        "policies": {
            "forge_policy_name": TOWERFORGE_POLICY_NAMES["forge"],
            "launch_policy_name": TOWERFORGE_POLICY_NAMES["launch"],
            "s3_policy_name": TOWERFORGE_POLICY_NAMES["s3"],
        },
    }
