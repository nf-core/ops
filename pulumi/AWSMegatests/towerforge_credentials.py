"""TowerForge IAM credentials management module

This module creates and manages IAM resources for TowerForge AWS operations,
including policies for Forge operations, Launch operations, and S3 bucket access.
"""

import json
import pulumi
import pulumi_aws as aws


def create_towerforge_credentials(aws_provider: aws.Provider, s3_bucket) -> tuple:
    """Create TowerForge IAM resources and return access key credentials.

    Creates IAM policies, user, and access keys for TowerForge operations.
    Based on https://github.com/seqeralabs/nf-tower-aws

    Args:
        aws_provider: Configured AWS provider instance
        s3_bucket: S3 bucket resource for policy attachment

    Returns:
        tuple: (access_key_id, access_key_secret) for use by seqerakit
    """

    # TowerForge Forge Policy - Comprehensive permissions for resource creation
    towerforge_forge_policy = aws.iam.Policy(
        "towerforge-forge-policy",
        name="TowerForge-Forge-Policy",
        description="IAM policy for TowerForge to create and manage AWS Batch resources",
        policy=json.dumps(
            {
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
                            "ec2:DescribeSubnets",
                            "ec2:DescribeLaunchTemplates",
                            "ec2:DescribeKeyPairs",
                            "ec2:DescribeVpcs",
                            "ec2:DescribeInstanceTypes",
                            "ec2:CreateLaunchTemplate",
                            "ec2:DeleteLaunchTemplate",
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
        ),
        opts=pulumi.ResourceOptions(provider=aws_provider),
    )

    # TowerForge Launch Policy - Limited permissions for pipeline execution
    towerforge_launch_policy = aws.iam.Policy(
        "towerforge-launch-policy",
        name="TowerForge-Launch-Policy",
        description="IAM policy for TowerForge to launch and monitor pipeline executions",
        policy=json.dumps(
            {
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
        ),
        opts=pulumi.ResourceOptions(provider=aws_provider),
    )

    # TowerForge S3 Bucket Access Policy - Access to specified S3 bucket
    towerforge_s3_policy = aws.iam.Policy(
        "towerforge-s3-policy",
        name="TowerForge-S3-Policy",
        description="IAM policy for TowerForge to access nf-core-awsmegatests S3 bucket",
        policy=s3_bucket.arn.apply(
            lambda arn: json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": ["s3:ListBucket"],
                            "Resource": [arn],
                        },
                        {
                            "Action": [
                                "s3:GetObject",
                                "s3:PutObject",
                                "s3:PutObjectTagging",
                                "s3:DeleteObject",
                            ],
                            "Resource": [f"{arn}/*"],
                            "Effect": "Allow",
                        },
                    ],
                }
            )
        ),
        opts=pulumi.ResourceOptions(provider=aws_provider, depends_on=[s3_bucket]),
    )

    # Create TowerForge IAM User
    towerforge_user = aws.iam.User(
        "towerforge-user",
        name="TowerForge-AWSMegatests",
        opts=pulumi.ResourceOptions(provider=aws_provider),
    )

    # Attach policies to the TowerForge user
    towerforge_forge_policy_attachment = aws.iam.UserPolicyAttachment(
        "towerforge-forge-policy-attachment",
        user=towerforge_user.name,
        policy_arn=towerforge_forge_policy.arn,
        opts=pulumi.ResourceOptions(
            provider=aws_provider, depends_on=[towerforge_user, towerforge_forge_policy]
        ),
    )

    towerforge_launch_policy_attachment = aws.iam.UserPolicyAttachment(
        "towerforge-launch-policy-attachment",
        user=towerforge_user.name,
        policy_arn=towerforge_launch_policy.arn,
        opts=pulumi.ResourceOptions(
            provider=aws_provider,
            depends_on=[towerforge_user, towerforge_launch_policy],
        ),
    )

    towerforge_s3_policy_attachment = aws.iam.UserPolicyAttachment(
        "towerforge-s3-policy-attachment",
        user=towerforge_user.name,
        policy_arn=towerforge_s3_policy.arn,
        opts=pulumi.ResourceOptions(
            provider=aws_provider, depends_on=[towerforge_user, towerforge_s3_policy]
        ),
    )

    # Create access keys for the TowerForge user
    towerforge_access_key = aws.iam.AccessKey(
        "towerforge-access-key",
        user=towerforge_user.name,
        opts=pulumi.ResourceOptions(
            provider=aws_provider,
            depends_on=[
                towerforge_forge_policy_attachment,
                towerforge_launch_policy_attachment,
                towerforge_s3_policy_attachment,
            ],
            additional_secret_outputs=["secret"],
        ),
    )

    # Return the access key credentials for use by seqerakit
    return towerforge_access_key.id, towerforge_access_key.secret


def get_towerforge_resources(aws_provider: aws.Provider, s3_bucket) -> dict:
    """Create TowerForge resources and return resource information for exports.

    This function creates the TowerForge IAM resources and returns a dictionary
    containing resource information for Pulumi exports.

    Args:
        aws_provider: Configured AWS provider instance
        s3_bucket: S3 bucket resource for policy attachment

    Returns:
        dict: Resource information for Pulumi exports
    """
    # Create the credentials (this will create all the resources)
    access_key_id, access_key_secret = create_towerforge_credentials(
        aws_provider, s3_bucket
    )

    # Get references to the created resources for export
    # Note: We need to reference the resources by their logical names since they're created
    # in the create_towerforge_credentials function

    return {
        "user": {
            "name": "TowerForge-AWSMegatests",
            "arn": "arn:aws:iam::{aws_account_id}:user/TowerForge-AWSMegatests",  # Will be populated by Pulumi
        },
        "access_key_id": access_key_id,
        "access_key_secret": access_key_secret,
        "policies": {
            "forge_policy_name": "TowerForge-Forge-Policy",
            "launch_policy_name": "TowerForge-Launch-Policy",
            "s3_policy_name": "TowerForge-S3-Policy",
        },
    }
