#!/usr/bin/env python

import yaml

import pulumi
import pulumi_github as github

nf_core = github.Repository(
    "nf-core",
    default_branch="master",
    description="A small example pipeline used to test new nf-core infrastructure and common code.",
    has_downloads=True,
    has_issues=True,
    has_projects=True,
    has_wiki=True,
    name="testpipeline",
    security_and_analysis=github.RepositorySecurityAndAnalysisArgs(
        secret_scanning=github.RepositorySecurityAndAnalysisSecretScanningArgs(
            status="disabled",
        ),
        secret_scanning_push_protection=github.RepositorySecurityAndAnalysisSecretScanningPushProtectionArgs(
            status="disabled",
        ),
    ),
    visibility="public",
    opts=pulumi.ResourceOptions(protect=True),
)
