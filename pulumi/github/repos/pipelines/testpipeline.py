import pulumi
import pulumi_github as github

NAME = "testpipeline"

TOPICS = [
    "nextflow",
    "pipelines",
    "nf-test",
    "modules",
    "nf-core",
    "dsl2",
    "workflows",
]

nfcore_testpipeline = github.Repository(
    NAME,
    default_branch="master",
    description="A small example pipeline used to test new nf-core infrastructure and common code.",
    has_downloads=True,
    has_issues=True,
    has_projects=True,
    has_wiki=False,
    homepage_url=f"https://nf-co.re/{NAME}",
    name=NAME,
    security_and_analysis=github.RepositorySecurityAndAnalysisArgs(
        secret_scanning=github.RepositorySecurityAndAnalysisSecretScanningArgs(
            status="disabled",
        ),
        secret_scanning_push_protection=github.RepositorySecurityAndAnalysisSecretScanningPushProtectionArgs(
            status="disabled",
        ),
    ),
    visibility="public",
    topics=TOPICS,
    opts=pulumi.ResourceOptions(protect=True),
)
