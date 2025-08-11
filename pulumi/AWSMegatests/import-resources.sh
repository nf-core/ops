#!/bin/bash

# Mass import script for existing AWS resources
set -e

echo "Starting mass import of existing AWS resources..."

# Import IAM policies
echo "Importing IAM policies..."
uv run pulumi import aws:iam/policy:Policy towerforge-launch-policy arn:aws:iam::728131696474:policy/TowerForge-Launch-Policy
uv run pulumi import aws:iam/policy:Policy towerforge-forge-policy arn:aws:iam::728131696474:policy/TowerForge-Forge-Policy
uv run pulumi import aws:iam/policy:Policy towerforge-s3-policy arn:aws:iam::728131696474:policy/TowerForge-S3-Policy

# Import IAM user
echo "Importing IAM user..."
uv run pulumi import aws:iam/user:User towerforge-user TowerForge-AWSMegatests

# Import access key (if it exists - you'll need the actual access key ID)
# echo "Importing IAM access key..."
# uv run pulumi import aws:iam/accessKey:AccessKey towerforge-access-key TowerForge-AWSMegatests:AKIA...

# Import policy attachments
echo "Importing policy attachments..."
uv run pulumi import aws:iam/userPolicyAttachment:UserPolicyAttachment towerforge-launch-attachment TowerForge-AWSMegatests/arn:aws:iam::728131696474:policy/TowerForge-Launch-Policy
uv run pulumi import aws:iam/userPolicyAttachment:UserPolicyAttachment towerforge-forge-attachment TowerForge-AWSMegatests/arn:aws:iam::728131696474:policy/TowerForge-Forge-Policy
uv run pulumi import aws:iam/userPolicyAttachment:UserPolicyAttachment towerforge-s3-attachment TowerForge-AWSMegatests/arn:aws:iam::728131696474:policy/TowerForge-S3-Policy

echo "Mass import complete! Running preview to check status..."
uv run pulumi preview