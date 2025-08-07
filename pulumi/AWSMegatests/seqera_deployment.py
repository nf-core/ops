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
            return f'tw --access-token="{token}" compute-envs list --workspace=nf-core/AWSmegatests | grep "{grep_pattern}" | awk \'{{print $1}}\''

        return command.local.Command(
            f"query-{env_name}-compute-env",
            create=tower_access_token.apply(create_query_cmd),
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

    # Extract the IDs from the query results
    compute_env_ids = {
        "cpu": cpu_query_cmd.stdout.apply(lambda x: x.strip()),
        "gpu": gpu_query_cmd.stdout.apply(lambda x: x.strip()),
        "arm": arm_query_cmd.stdout.apply(lambda x: x.strip()),
    }

    return compute_env_ids
