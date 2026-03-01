#!/usr/bin/env python3
"""Discover AWS resources for Pulumi import.

This script discovers AWS resources matching specified criteria and generates
a Pulumi import JSON file for bulk import operations.

Usage:
    python discover-aws-resources.py --region eu-west-1 --resource-type s3
    python discover-aws-resources.py --prefix nf-core- --output resources.json
"""

import boto3
import json
import argparse
import sys
from typing import List, Dict


def discover_s3_buckets(region: str, prefix: str = "nf-core-") -> List[Dict]:
    """Discover S3 buckets matching prefix.

    Args:
        region: AWS region
        prefix: Bucket name prefix filter

    Returns:
        List of resource dictionaries for import
    """
    print(f"Discovering S3 buckets in {region} with prefix '{prefix}'...")

    s3 = boto3.client("s3", region_name=region)
    resources = []

    try:
        buckets = s3.list_buckets()["Buckets"]

        for bucket in buckets:
            if not bucket["Name"].startswith(prefix):
                continue

            resource_name = bucket["Name"].replace(prefix, "").replace("-", "_")
            print(f"  Found bucket: {bucket['Name']}")

            # Main bucket
            resources.append(
                {
                    "type": "aws:s3/bucket:Bucket",
                    "name": f"{resource_name}_bucket",
                    "id": bucket["Name"],
                }
            )

            # Try to discover bucket configurations
            try:
                # Versioning
                versioning = s3.get_bucket_versioning(Bucket=bucket["Name"])
                if versioning.get("Status") == "Enabled":
                    print("    - Versioning enabled")
                    resources.append(
                        {
                            "type": "aws:s3/bucketVersioningV2:BucketVersioningV2",
                            "name": f"{resource_name}_versioning",
                            "id": bucket["Name"],
                        }
                    )

                # Encryption
                encryption = s3.get_bucket_encryption(Bucket=bucket["Name"])
                if encryption.get("ServerSideEncryptionConfiguration"):
                    print("    - Encryption configured")
                    resources.append(
                        {
                            "type": "aws:s3/bucketServerSideEncryptionConfigurationV2:BucketServerSideEncryptionConfigurationV2",
                            "name": f"{resource_name}_encryption",
                            "id": bucket["Name"],
                        }
                    )

                # Public Access Block
                public_block = s3.get_public_access_block(Bucket=bucket["Name"])
                if public_block.get("PublicAccessBlockConfiguration"):
                    print("    - Public access block configured")
                    resources.append(
                        {
                            "type": "aws:s3/bucketPublicAccessBlock:BucketPublicAccessBlock",
                            "name": f"{resource_name}_public_block",
                            "id": bucket["Name"],
                        }
                    )

            except s3.exceptions.ClientError as e:
                # Configuration not set or permission denied
                if "ServerSideEncryptionConfigurationNotFoundError" in str(e):
                    pass
                elif "NoSuchPublicAccessBlockConfiguration" in str(e):
                    pass
                else:
                    print(f"    Warning: Could not check configurations: {e}")

    except Exception as e:
        print(f"Error discovering S3 buckets: {e}", file=sys.stderr)

    return resources


def discover_iam_users(region: str, prefix: str = "nf-core-") -> List[Dict]:
    """Discover IAM users matching prefix.

    Args:
        region: AWS region (IAM is global but client needs region)
        prefix: User name prefix filter

    Returns:
        List of resource dictionaries for import
    """
    print(f"Discovering IAM users with prefix '{prefix}'...")

    iam = boto3.client("iam", region_name=region)
    resources = []

    try:
        users = iam.list_users()["Users"]

        for user in users:
            if not user["UserName"].startswith(prefix):
                continue

            resource_name = user["UserName"].replace(prefix, "").replace("-", "_")
            print(f"  Found user: {user['UserName']}")

            # User
            resources.append(
                {
                    "type": "aws:iam/user:User",
                    "name": f"{resource_name}_user",
                    "id": user["UserName"],
                }
            )

            # Attached policies
            try:
                policies = iam.list_attached_user_policies(UserName=user["UserName"])
                for policy in policies["AttachedPolicies"]:
                    # Only custom policies (not AWS managed)
                    if not policy["PolicyArn"].startswith("arn:aws:iam::aws:"):
                        policy_name = policy["PolicyName"].replace("-", "_")
                        print(f"    - Policy: {policy['PolicyName']}")

                        resources.append(
                            {
                                "type": "aws:iam/policy:Policy",
                                "name": f"{policy_name}_policy",
                                "id": policy["PolicyArn"],
                            }
                        )

                        resources.append(
                            {
                                "type": "aws:iam/userPolicyAttachment:UserPolicyAttachment",
                                "name": f"{resource_name}_{policy_name}_attachment",
                                "id": f"{user['UserName']}/{policy['PolicyArn']}",
                            }
                        )

            except Exception as e:
                print(f"    Warning: Could not check policies: {e}")

    except Exception as e:
        print(f"Error discovering IAM users: {e}", file=sys.stderr)

    return resources


def discover_iam_roles(region: str, prefix: str = "nf-core-") -> List[Dict]:
    """Discover IAM roles matching prefix.

    Args:
        region: AWS region (IAM is global but client needs region)
        prefix: Role name prefix filter

    Returns:
        List of resource dictionaries for import
    """
    print(f"Discovering IAM roles with prefix '{prefix}'...")

    iam = boto3.client("iam", region_name=region)
    resources = []

    try:
        roles = iam.list_roles()["Roles"]

        for role in roles:
            if not role["RoleName"].startswith(prefix):
                continue

            resource_name = role["RoleName"].replace(prefix, "").replace("-", "_")
            print(f"  Found role: {role['RoleName']}")

            # Role
            resources.append(
                {
                    "type": "aws:iam/role:Role",
                    "name": f"{resource_name}_role",
                    "id": role["RoleName"],
                }
            )

            # Attached policies
            try:
                policies = iam.list_attached_role_policies(RoleName=role["RoleName"])
                for policy in policies["AttachedPolicies"]:
                    # Only custom policies (not AWS managed)
                    if not policy["PolicyArn"].startswith("arn:aws:iam::aws:"):
                        policy_name = policy["PolicyName"].replace("-", "_")
                        print(f"    - Policy: {policy['PolicyName']}")

                        resources.append(
                            {
                                "type": "aws:iam/policy:Policy",
                                "name": f"{policy_name}_policy",
                                "id": policy["PolicyArn"],
                            }
                        )

                        resources.append(
                            {
                                "type": "aws:iam/rolePolicyAttachment:RolePolicyAttachment",
                                "name": f"{resource_name}_{policy_name}_attachment",
                                "id": f"{role['RoleName']}/{policy['PolicyArn']}",
                            }
                        )

            except Exception as e:
                print(f"    Warning: Could not check policies: {e}")

    except Exception as e:
        print(f"Error discovering IAM roles: {e}", file=sys.stderr)

    return resources


def generate_import_json(resources: List[Dict], output_file: str) -> None:
    """Generate Pulumi import JSON file.

    Args:
        resources: List of resource dictionaries
        output_file: Output file path
    """
    import_data = {"resources": resources}

    with open(output_file, "w") as f:
        json.dump(import_data, f, indent=2)

    print(f"\n✓ Generated import file: {output_file}")
    print(f"✓ Found {len(resources)} resources to import")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Discover AWS resources for Pulumi import",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Discover all nf-core S3 buckets
  python discover-aws-resources.py --region eu-west-1 --resource-type s3

  # Discover all IAM resources
  python discover-aws-resources.py --resource-type iam

  # Discover everything with custom prefix
  python discover-aws-resources.py --prefix myproject- --resource-type all

  # Save to custom file
  python discover-aws-resources.py --output custom-import.json
        """,
    )

    parser.add_argument(
        "--region", default="us-east-1", help="AWS region (default: us-east-1)"
    )

    parser.add_argument(
        "--prefix",
        default="nf-core-",
        help="Resource name prefix filter (default: nf-core-)",
    )

    parser.add_argument(
        "--resource-type",
        choices=["s3", "iam-users", "iam-roles", "iam", "all"],
        default="all",
        help="Type of resources to discover (default: all)",
    )

    parser.add_argument(
        "--output",
        default="discovered-resources.json",
        help="Output JSON file (default: discovered-resources.json)",
    )

    args = parser.parse_args()

    # Verify AWS credentials
    try:
        sts = boto3.client("sts", region_name=args.region)
        identity = sts.get_caller_identity()
        print(f"AWS Account: {identity['Account']}")
        print(f"AWS User: {identity['Arn']}\n")
    except Exception as e:
        print(f"Error: Could not verify AWS credentials: {e}", file=sys.stderr)
        sys.exit(1)

    # Discover resources
    resources = []

    if args.resource_type in ["s3", "all"]:
        resources.extend(discover_s3_buckets(args.region, args.prefix))

    if args.resource_type in ["iam-users", "iam", "all"]:
        resources.extend(discover_iam_users(args.region, args.prefix))

    if args.resource_type in ["iam-roles", "iam", "all"]:
        resources.extend(discover_iam_roles(args.region, args.prefix))

    if not resources:
        print("\nNo resources found matching criteria.")
        sys.exit(0)

    # Generate import file
    generate_import_json(resources, args.output)

    # Print next steps
    print("\nNext steps:")
    print(f"  1. Review {args.output}")
    print(f"  2. Run: uv run pulumi import -f {args.output} -o imported.py -y")
    print("  3. Add generated code to your Pulumi program")
    print("  4. Verify: uv run pulumi preview")


if __name__ == "__main__":
    main()
