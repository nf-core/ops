import {
  to = aws_iam_user.towerforge
  id = "TowerForge-AWSMegatests"
}

resource "aws_iam_user" "towerforge" {
  name = "TowerForge-AWSMegatests"
}

import {
  to = aws_iam_policy.towerforge_forge
  id = "arn:aws:iam::728131696474:policy/TowerForge-Forge-Policy"
}

resource "aws_iam_policy" "towerforge_forge" {
  name        = "TowerForge-Forge-Policy"
  description = "IAM policy for TowerForge to create and manage AWS Batch resources"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "TowerForge0"
        Effect = "Allow"
        Action = [
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
        ]
        Resource = "*"
      },
      {
        Sid    = "TowerLaunch0"
        Effect = "Allow"
        Action = [
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
        ]
        Resource = "*"
      },
    ]
  })
}

import {
  to = aws_iam_policy.towerforge_launch
  id = "arn:aws:iam::728131696474:policy/TowerForge-Launch-Policy"
}

resource "aws_iam_policy" "towerforge_launch" {
  name        = "TowerForge-Launch-Policy"
  description = "IAM policy for TowerForge to launch and monitor pipeline executions"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "TowerLaunch0"
        Effect = "Allow"
        Action = [
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
        ]
        Resource = "*"
      },
    ]
  })
}

import {
  to = aws_iam_policy.towerforge_s3
  id = "arn:aws:iam::728131696474:policy/TowerForge-S3-Policy"
}

resource "aws_iam_policy" "towerforge_s3" {
  name        = "TowerForge-S3-Policy"
  description = "IAM policy for TowerForge to access ${aws_s3_bucket.nf_core_awsmegatests.bucket} S3 bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = [aws_s3_bucket.nf_core_awsmegatests.arn]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:PutObjectTagging",
          "s3:DeleteObject",
        ]
        Resource = ["${aws_s3_bucket.nf_core_awsmegatests.arn}/*"]
      },
    ]
  })
}

import {
  to = aws_iam_user_policy_attachment.towerforge_forge
  id = "TowerForge-AWSMegatests/arn:aws:iam::728131696474:policy/TowerForge-Forge-Policy"
}

resource "aws_iam_user_policy_attachment" "towerforge_forge" {
  user       = aws_iam_user.towerforge.name
  policy_arn = aws_iam_policy.towerforge_forge.arn
}

import {
  to = aws_iam_user_policy_attachment.towerforge_launch
  id = "TowerForge-AWSMegatests/arn:aws:iam::728131696474:policy/TowerForge-Launch-Policy"
}

resource "aws_iam_user_policy_attachment" "towerforge_launch" {
  user       = aws_iam_user.towerforge.name
  policy_arn = aws_iam_policy.towerforge_launch.arn
}

import {
  to = aws_iam_user_policy_attachment.towerforge_s3
  id = "TowerForge-AWSMegatests/arn:aws:iam::728131696474:policy/TowerForge-S3-Policy"
}

resource "aws_iam_user_policy_attachment" "towerforge_s3" {
  user       = aws_iam_user.towerforge.name
  policy_arn = aws_iam_policy.towerforge_s3.arn
}

resource "aws_iam_access_key" "towerforge" {
  user = aws_iam_user.towerforge.name
}
