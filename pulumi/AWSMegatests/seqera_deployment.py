"""Seqera Platform compute environment deployment using seqerakit"""

import json
import pulumi
import pulumi_command as command


def deploy_seqera_environments(
    secrets, towerforge_access_key_id, towerforge_access_key_secret
):
    """Deploy Seqera Platform compute environments using seqerakit"""

    # Deploy seqerakit environments and extract compute IDs
    # NOTE: We could check for tw-cli availability here, but we'll let seqerakit
    # throw the appropriate error if it's missing. Seqerakit requires tw-cli to be
    # installed and available in PATH.
    #
    # NOTE: Seqerakit will create and manage:
    # - AWS Batch compute environments and job queues
    # - IAM roles (ExecutionRole, FargateRole) with TowerForge prefix
    # - Security groups and networking resources
    # These are managed by Seqera Platform and should not be imported into Pulumi
    seqerakit_environment = {
        "TOWER_ACCESS_TOKEN": secrets["tower_access_token"],
        "TOWER_WORKSPACE_ID": secrets["tower_workspace_id"],
        "ORGANIZATION_NAME": "nf-core",
        "WORKSPACE_NAME": "AWSmegatests",
        "AWS_CREDENTIALS_NAME": "tower-awstest",
        "AWS_REGION": "eu-west-1",
        "AWS_WORK_DIR": "s3://nf-core-awsmegatests",
        "AWS_COMPUTE_ENV_ALLOWED_BUCKETS": "s3://ngi-igenomes,s3://annotation-cache",
        # Use TowerForge AWS credentials for seqerakit operations (credential separation)
        # These credentials have the specific permissions needed for AWS Batch operations
        "AWS_ACCESS_KEY_ID": towerforge_access_key_id,
        "AWS_SECRET_ACCESS_KEY": towerforge_access_key_secret,
        # Tower CLI configuration - use standard Seqera Cloud endpoint
        "TOWER_API_ENDPOINT": "https://api.cloud.seqera.io",
    }

    # Read JSON config files to make them dependencies
    with open("seqerakit/current-env-cpu.json", "r") as f:
        cpu_config = json.load(f)
    with open("seqerakit/current-env-gpu.json", "r") as f:
        gpu_config = json.load(f)
    with open("seqerakit/current-env-cpu-arm.json", "r") as f:
        arm_config = json.load(f)

    # Deploy CPU environment with seqerakit (with JSON output)
    # NOTE: Tower access token needs to be valid and have permissions for nf-core/AWSmegatests workspace
    cpu_deploy_cmd = command.local.Command(
        "deploy-cpu-environment",
        create=pulumi.Output.concat(
            "cd seqerakit && uv run seqerakit --json aws_ireland_fusionv2_nvme_cpu_current.yml # Config hash: ",
            str(hash(json.dumps(cpu_config, sort_keys=True))),
        ),
        environment=seqerakit_environment,
        opts=pulumi.ResourceOptions(additional_secret_outputs=["stdout"]),
    )

    # Deploy GPU environment with seqerakit (with JSON output)
    gpu_deploy_cmd = command.local.Command(
        "deploy-gpu-environment",
        create=pulumi.Output.concat(
            "cd seqerakit && uv run seqerakit --json aws_ireland_fusionv2_nvme_gpu_current.yml # Config hash: ",
            str(hash(json.dumps(gpu_config, sort_keys=True))),
        ),
        environment=seqerakit_environment,
        opts=pulumi.ResourceOptions(
            additional_secret_outputs=["stdout"], depends_on=[cpu_deploy_cmd]
        ),
    )

    # Deploy ARM environment with seqerakit (with JSON output)
    arm_deploy_cmd = command.local.Command(
        "deploy-arm-environment",
        create=pulumi.Output.concat(
            "cd seqerakit && uv run seqerakit --json aws_ireland_fusionv2_nvme_cpu_arm_current.yml # Config hash: ",
            str(hash(json.dumps(arm_config, sort_keys=True))),
        ),
        environment=seqerakit_environment,
        opts=pulumi.ResourceOptions(
            additional_secret_outputs=["stdout"], depends_on=[gpu_deploy_cmd]
        ),
    )

    return {
        "cpu_deploy_cmd": cpu_deploy_cmd,
        "gpu_deploy_cmd": gpu_deploy_cmd,
        "arm_deploy_cmd": arm_deploy_cmd,
        "environment": seqerakit_environment,
    }


def query_compute_environment_ids(tower_access_token):
    """Query existing compute environment IDs directly from Seqera Platform"""

    def create_query_command(env_name: str, grep_pattern: str):
        def create_query_cmd(token: str) -> str:
            # Enhanced command with better error handling and debugging
            return f'''
            echo "Querying {env_name} compute environment..." >&2
            result=$(tw --access-token="{token}" compute-envs list --workspace=nf-core/AWSmegatests 2>&1)
            if [ $? -ne 0 ]; then
                echo "Error querying Tower CLI: $result" >&2
                echo "tower-query-failed-{env_name}"
                exit 1
            fi
            
            env_id=$(echo "$result" | grep "{grep_pattern}" | awk '{{print $1}}' | head -1)
            if [ -z "$env_id" ]; then
                echo "No compute environment found matching pattern: {grep_pattern}" >&2
                echo "Available compute environments:" >&2
                echo "$result" >&2
                echo "no-match-{env_name}-{grep_pattern}"
                exit 1
            fi
            
            echo "$env_id"
            '''

        # Handle both string and Pulumi Output types
        if hasattr(tower_access_token, "apply"):
            # It's a Pulumi Output
            create_cmd = tower_access_token.apply(create_query_cmd)
        else:
            # It's a regular string
            create_cmd = create_query_cmd(tower_access_token)

        return command.local.Command(
            f"query-{env_name}-compute-env",
            create=create_cmd,
            # Remove additional_secret_outputs to make the compute env IDs visible in variables
        )

    cpu_query_cmd = create_query_command(
        "cpu", "aws_ireland_fusionv2_nvme_cpu_snapshots"
    )
    gpu_query_cmd = create_query_command(
        "gpu", "aws_ireland_fusionv2_nvme_gpu_snapshots"
    )
    arm_query_cmd = create_query_command(
        "arm", "aws_ireland_fusionv2_nvme_cpu_ARM_snapshots"
    )

    # Extract the IDs from the query results with validation
    def validate_env_id(env_name: str, env_id: str) -> str:
        """Validate compute environment ID and provide fallback"""
        env_id = env_id.strip()

        # Check for error patterns
        if env_id.startswith("tower-query-failed-") or env_id.startswith("no-match-"):
            pulumi.log.warn(f"Failed to query {env_name} compute environment: {env_id}")
            return f"query-failed-{env_name}"

        # Check for valid UUID-like format (compute env IDs are typically long alphanumeric)
        if len(env_id) < 10 or not env_id.replace("-", "").isalnum():
            pulumi.log.warn(
                f"Invalid {env_name} compute environment ID format: {env_id}"
            )
            return f"invalid-format-{env_name}"

        return env_id

    compute_env_ids = {
        "cpu": cpu_query_cmd.stdout.apply(lambda x: validate_env_id("cpu", x)),
        "gpu": gpu_query_cmd.stdout.apply(lambda x: validate_env_id("gpu", x)),
        "arm": arm_query_cmd.stdout.apply(lambda x: validate_env_id("arm", x)),
    }

    return compute_env_ids
