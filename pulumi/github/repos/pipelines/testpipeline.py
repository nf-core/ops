# NOTE => are tests from PHP
# TODO Convert => to actual tests https://www.pulumi.com/docs/using-pulumi/testing/
# https://github.com/pulumi/examples/blob/74db62a03d013c2854d2cf933c074ea0a3bbf69d/testing-unit-py/test_ec2.py
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
    description="A small example pipeline used to test new nf-core infrastructure and common code.",  # 'repo_description' => 'Description must be set',
    has_downloads=True,
    has_issues=True,  # 'repo_issues' => 'Enable issues',
    has_projects=True,
    has_wiki=False,  # 'repo_wikis' => 'Disable wikis',
    allow_merge_commit=True,  # 'repo_merge_commits' => 'Allow merge commits',
    allow_rebase_merge=True,  # 'repo_merge_rebase' => 'Allow rebase merging',
    allow_squash_merge=False,  # 'repo_merge_squash' => 'Do not allow squash merges',
    delete_branch_on_merge=True,
    homepage_url=f"https://nf-co.re/{NAME}",  # 'repo_url' => 'URL should be set to https://nf-co.re',
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
    topics=TOPICS,  # 'repo_keywords' => 'Minimum keywords set',
    opts=pulumi.ResourceOptions(protect=True),
)

# TODO Names of required CI checks. These are added to whatever already exists.
# public $required_status_check_contexts = [
#     'pre-commit',
#     'nf-core',

# Make branches foreach (['master', 'dev', 'TEMPLATE'] as $branch) {
# 'repo_default_branch' => 'default branch master (released) or dev (no releases)',
# TODO Toggle this on dev and master?
# 'branch_master_exists' => 'master branch: branch must exist',
branch_default_testpipeline = github.BranchDefault(
    f"branch_default_{NAME}",
    branch="master",
    repository={NAME},
    opts=pulumi.ResourceOptions(protect=True),
)
# 'branch_dev_exists' => 'dev branch: branch must exist',
branch_dev_testpipeline = github.Branch(
    "branch_dev_testpipeline",
    branch="dev",
    repository="testpipeline",
    opts=pulumi.ResourceOptions(protect=True),
)
# 'branch_template_exists' => 'TEMPLATE branch: branch must exist',
branch_template_testpipeline = github.Branch(
    "branch_template_testpipeline",
    branch="TEMPLATE",
    repository="testpipeline",
    opts=pulumi.ResourceOptions(protect=True),
)
# TODO Add branch protections https://github.com/nf-core/website/blob/33acd6a2fab2bf9251e14212ce731ef3232b5969/public_html/pipeline_health.php#L296
# TODO Template branch protection https://github.com/nf-core/website/blob/33acd6a2fab2bf9251e14212ce731ef3232b5969/public_html/pipeline_health.php#L509
# https://github.com/nf-core/website/blob/33acd6a2fab2bf9251e14212ce731ef3232b5969/public_html/pipeline_health.php#L275-L278
# TODO Set contributors to push
# TODO Set core to admin
# TODO 'team_contributors' => 'Write access for nf-core/contributors',
# TODO 'team_core' => 'Admin access for nf-core/core',
# TODO 'branch_master_strict_updates' => 'master branch: do not require branch to be up to date before merging',
# TODO 'branch_master_required_ci' => 'master branch: minimum set of CI tests must pass',
# TODO 'branch_master_stale_reviews' => 'master branch: reviews not marked stale after new commits',
# TODO 'branch_master_code_owner_reviews' => 'master branch: code owner reviews not required',
# TODO 'branch_master_required_num_reviews' => 'master branch: 2 reviews required',
# TODO 'branch_master_enforce_admins' => 'master branch: do not enforce rules for admins',
# TODO 'branch_dev_strict_updates' => 'dev branch: do not require branch to be up to date before merging',
# TODO 'branch_dev_required_ci' => 'dev branch: minimum set of CI tests must pass',
# TODO 'branch_dev_stale_reviews' => 'dev branch: reviews not marked stale after new commits',
# TODO 'branch_dev_code_owner_reviews' => 'dev branch: code owner reviews not required',
# TODO 'branch_dev_required_num_reviews' => 'dev branch: 1 review required',
# TODO 'branch_dev_enforce_admins' => 'dev branch: do not enforce rules for admins',
# TODO 'branch_template_restrict_push' => 'Restrict push to TEMPLATE to @nf-core-bot',
