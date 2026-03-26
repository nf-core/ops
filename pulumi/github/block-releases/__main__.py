import pulumi
import pulumi_github as github
from github import Auth, Github

github_config = pulumi.Config("github")
token = github_config.require("token")
owner = github_config.get("owner") or "nf-core"
config = pulumi.Config()
repos_filter = config.get("repos")  # optional comma-separated list of repos

# Fetch all non-archived repos in the org with dev as default branch
gh = Github(auth=Auth.Token(token))
org = gh.get_organization(owner)
dev_repos = [
    repo.name
    for repo in org.get_repos(type="all")
    if repo.default_branch == "dev" and not repo.archived
]

if repos_filter:
    allowed = {r.strip() for r in repos_filter.split(",")}
    dev_repos = [r for r in dev_repos if r in allowed]

pulumi.log.info(f"Found {len(dev_repos)} repos with dev as default branch")

for repo_name in dev_repos:
    github.RepositoryRuleset(
        f"{repo_name}-block-releases",
        name="block-releases",
        repository=repo_name,
        target="tag",
        enforcement="active",
        conditions=github.RepositoryRulesetConditionsArgs(
            ref_name=github.RepositoryRulesetConditionsRefNameArgs(
                includes=["~ALL"],
                excludes=[],
            ),
        ),
        bypass_actors=[
            github.RepositoryRulesetBypassActorArgs(
                actor_id=1,
                actor_type="OrganizationAdmin",
                bypass_mode="always",
            ),
        ],
        rules=github.RepositoryRulesetRulesArgs(
            creation=True,
            deletion=True,
            non_fast_forward=True,
        ),
    )
