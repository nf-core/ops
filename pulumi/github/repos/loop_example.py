#!/usr/bin/env python

import yaml

import pulumi
import pulumi_github as github

TOPICS = [
    "nextflow",
    "pipelines",
    "nf-test",
    "modules",
    "nf-core",
    "dsl2",
    "workflows",
]

alpha_test_pipeline_repos = [
    "denovotranscript",
    "meerpipe",
    "pairgenomealign",
    "phaseimpute",
    "reportho",
]

for pipeline in alpha_test_pipeline_repos:
    github.Repository(
        pipeline,
        allow_merge_commit=True,
        allow_rebase_merge=True,
        allow_squash_merge=True,
        default_branch="master",
        description="Alpha test repository for nf-core",
        has_downloads=True,
        has_issues=True,
        has_projects=True,
        homepage_url=f"https://nf-co.re/{pipeline}",
        merge_commit_message="",
        merge_commit_title="",
        name=pipeline,
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
        topics=TOPICS,
        visibility="public",
        # NOTE Idk if this will work
        opts=pulumi.ResourceOptions(protect=True),
    )
