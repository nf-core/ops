import yaml

import pulumi
import pulumi_github as github


nf_core_tf = github.Repository(
    "nf-core-tf",
    allow_merge_commit=False,
    allow_rebase_merge=False,
    allow_squash_merge=False,
    default_branch="main",
    description="Repository to host tool-specific module files for the Nextflow DSL2 community!",
    has_downloads=True,
    has_issues=True,
    has_projects=False,
    homepage_url="https://nf-co.re",
    merge_commit_message="",
    merge_commit_title="",
    name="modules",
    security_and_analysis=github.RepositorySecurityAndAnalysisArgs(
        secret_scanning=github.RepositorySecurityAndAnalysisSecretScanningArgs(
            status="disabled",
        ),
        secret_scanning_push_protection=github.RepositorySecurityAndAnalysisSecretScanningPushProtectionArgs(
            status="disabled",
        ),
    ),
    squash_merge_commit_message="",
    squash_merge_commit_title="",
    topics=[
        "nextflow",
        "pipelines",
        "nf-test",
        "modules",
        "nf-core",
        "dsl2",
        "workflows",
    ],
    visibility="public",
    opts=pulumi.ResourceOptions(protect=True),
)
