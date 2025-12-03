# Pulumi GitHub Provider Guide

Quick reference for managing GitHub resources with Pulumi.

## Table of Contents

- [Authentication](#authentication)
- [Common Resources](#common-resources)
- [Repository Management](#repository-management)
- [Secrets and Variables](#secrets-and-variables)
- [Teams and Permissions](#teams-and-permissions)
- [Best Practices](#best-practices)

## Authentication

### Using Personal Access Token

```bash
# Set via environment variable
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxx"

# Or via .envrc with 1Password
from_op GITHUB_TOKEN="op://Dev/GitHub-Token/credential"
```

### Configure Provider

```python
import pulumi_github as github

# Provider will use GITHUB_TOKEN from environment
# Or configure explicitly:
provider = github.Provider("github",
    token="ghp_xxxxxxxxxxxxx",
    owner="nf-core",
)
```

### Required Token Permissions

For managing repositories and secrets, token needs:

- `repo` - Full repository access
- `admin:org` - Organization management
- `workflow` - GitHub Actions workflow management

## Common Resources

### Create Repository

```python
import pulumi_github as github

repo = github.Repository(
    "my-repo",
    name="my-awesome-repo",
    description="Repository managed by Pulumi",
    visibility="public",  # or "private"
    has_issues=True,
    has_projects=True,
    has_wiki=True,
    auto_init=True,
    gitignore_template="Python",
    license_template="apache-2.0",
)

pulumi.export("repo_url", repo.html_url)
pulumi.export("clone_url", repo.ssh_clone_url)
```

### Repository with Protection Rules

```python
import pulumi_github as github

repo = github.Repository(
    "protected-repo",
    name="production-app",
    visibility="private",
)

# Branch protection for main
github.BranchProtection(
    "main-protection",
    repository_id=repo.node_id,
    pattern="main",
    required_pull_request_reviews=github.BranchProtectionRequiredPullRequestReviewsArgs(
        dismiss_stale_reviews=True,
        require_code_owner_reviews=True,
        required_approving_review_count=2,
    ),
    enforce_admins=True,
    require_signed_commits=True,
    required_status_checks=github.BranchProtectionRequiredStatusChecksArgs(
        strict=True,
        contexts=["ci/test", "ci/lint"],
    ),
)
```

## Repository Management

### Repository Settings

```python
import pulumi_github as github

repo = github.Repository(
    "configured-repo",
    name="my-repo",
    description="Fully configured repository",

    # Visibility
    visibility="public",

    # Features
    has_issues=True,
    has_projects=False,
    has_wiki=False,
    has_downloads=True,
    has_discussions=True,

    # Settings
    allow_merge_commit=True,
    allow_squash_merge=True,
    allow_rebase_merge=False,
    delete_branch_on_merge=True,

    # Security
    vulnerability_alerts=True,

    # Templates
    gitignore_template="Python",
    license_template="apache-2.0",

    # Topics
    topics=["python", "automation", "pulumi"],

    # Homepage
    homepage_url="https://example.com",
)
```

### Repository Collaborators

```python
import pulumi_github as github

# Add collaborator with specific permission
github.RepositoryCollaborator(
    "contributor",
    repository=repo.name,
    username="contributor-username",
    permission="push",  # pull, push, maintain, triage, admin
)

# Add team with access
github.TeamRepository(
    "team-access",
    team_id=team.id,
    repository=repo.name,
    permission="push",
)
```

### Repository Files

```python
import pulumi_github as github

# Create file in repository
github.RepositoryFile(
    "readme",
    repository=repo.name,
    file=".github/PULL_REQUEST_TEMPLATE.md",
    content="""## Description
Please include a summary of the changes.

## Testing
How has this been tested?
""",
    branch="main",
    commit_message="Add PR template",
    commit_author="Pulumi",
    commit_email="noreply@pulumi.com",
)
```

## Secrets and Variables

### Actions Secrets

```python
import pulumi_github as github
import pulumi

# Repository secret
github.ActionsSecret(
    "aws-key",
    repository=repo.name,
    secret_name="AWS_ACCESS_KEY_ID",
    plaintext_value=pulumi.Output.secret("AKIA..."),
)

# Organization secret (available to multiple repos)
github.ActionsOrganizationSecret(
    "org-secret",
    secret_name="ORG_WIDE_TOKEN",
    visibility="selected",  # all, private, selected
    selected_repository_ids=[repo1.repo_id, repo2.repo_id],
    plaintext_value=pulumi.Output.secret("secret-value"),
)

# Environment secret
github.ActionsEnvironmentSecret(
    "prod-secret",
    repository=repo.name,
    environment="production",
    secret_name="DATABASE_URL",
    plaintext_value=pulumi.Output.secret("postgres://..."),
)
```

### Actions Variables

```python
import pulumi_github as github

# Repository variable (non-sensitive)
github.ActionsVariable(
    "region",
    repository=repo.name,
    variable_name="AWS_REGION",
    value="us-east-1",
)

# Organization variable
github.ActionsOrganizationVariable(
    "org-var",
    variable_name="DEPLOY_ENV",
    value="production",
    visibility="selected",
    selected_repository_ids=[repo.repo_id],
)
```

### Example: Complete Secret Setup

```python
import pulumi_github as github
import pulumi

# AWS credentials for CI/CD
github.ActionsSecret(
    "aws-access-key",
    repository="modules",
    secret_name="CO2_REPORTS_AWS_ACCESS_KEY_ID",
    plaintext_value=access_key.id,
)

github.ActionsSecret(
    "aws-secret-key",
    repository="modules",
    secret_name="CO2_REPORTS_AWS_SECRET_ACCESS_KEY",
    plaintext_value=pulumi.Output.secret(access_key.secret),
)

github.ActionsVariable(
    "aws-region",
    repository="modules",
    variable_name="CO2_REPORTS_AWS_REGION",
    value="eu-north-1",
)
```

## Teams and Permissions

### Create Team

```python
import pulumi_github as github

team = github.Team(
    "platform-team",
    name="Platform Team",
    description="Infrastructure and DevOps team",
    privacy="closed",  # secret, closed
)

# Add team members
github.TeamMembership(
    "member1",
    team_id=team.id,
    username="user1",
    role="maintainer",  # member, maintainer
)
```

### Team Repository Access

```python
import pulumi_github as github

# Grant team access to repository
github.TeamRepository(
    "team-repo-access",
    team_id=team.id,
    repository=repo.name,
    permission="push",  # pull, triage, push, maintain, admin
)
```

## Best Practices

### Repository Naming

```python
# Use consistent naming
repo = github.Repository(
    "nf-co2-reports",  # Pulumi resource name
    name="nf-co2-reports",  # GitHub repo name
    description="CO2 footprint reporting infrastructure",
)
```

### Secret Management

```python
# Never hardcode secrets
# BAD:
plaintext_value="hardcoded-secret"

# GOOD: Use Pulumi secrets
plaintext_value=pulumi.Output.secret(secret_value)

# BETTER: Reference from 1Password via config
config = pulumi.Config()
secret = config.require_secret("github_token")
```

### Default Branch Protection

Always protect default branch:

```python
github.BranchProtection(
    "main-protection",
    repository_id=repo.node_id,
    pattern=repo.default_branch,
    required_pull_request_reviews=github.BranchProtectionRequiredPullRequestReviewsArgs(
        required_approving_review_count=1,
    ),
)
```

### Repository Templates

Use repository templates for consistency:

```python
# Template repository
template = github.Repository(
    "repo-template",
    name="repository-template",
    is_template=True,
    visibility="public",
)

# Create repo from template
new_repo = github.Repository(
    "from-template",
    name="new-project",
    template=github.RepositoryTemplateArgs(
        owner="nf-core",
        repository=template.name,
    ),
)
```

## Common Patterns

### Bulk Secret Creation

```python
import pulumi_github as github

secrets = {
    "AWS_ACCESS_KEY_ID": access_key_id,
    "AWS_SECRET_ACCESS_KEY": secret_access_key,
    "AWS_REGION": region,
}

for secret_name, secret_value in secrets.items():
    github.ActionsSecret(
        f"secret-{secret_name.lower()}",
        repository=repo.name,
        secret_name=secret_name,
        plaintext_value=pulumi.Output.secret(secret_value),
    )
```

### Environment-Based Configuration

```python
import pulumi

stack = pulumi.get_stack()

repo = github.Repository(
    f"app-{stack}",
    name=f"application-{stack}",
    visibility="private" if stack == "production" else "public",
)
```

### Webhook Configuration

```python
import pulumi_github as github

webhook = github.RepositoryWebhook(
    "ci-webhook",
    repository=repo.name,
    configuration=github.RepositoryWebhookConfigurationArgs(
        url="https://ci.example.com/webhook",
        content_type="json",
        insecure_ssl=False,
        secret=pulumi.Output.secret("webhook-secret"),
    ),
    events=["push", "pull_request"],
)
```

## Troubleshooting

### Token Permissions

If getting permission errors:

1. Verify token has required scopes
2. Check organization SSO requirements
3. Verify repository access

### Secret Not Updating

GitHub Actions secrets are write-only:

```python
# Force update with replace
github.ActionsSecret(
    "secret",
    repository=repo.name,
    secret_name="NAME",
    plaintext_value=new_value,
    opts=pulumi.ResourceOptions(replace_on_changes=["plaintext_value"]),
)
```

### Rate Limiting

GitHub API has rate limits:

- Use `--parallel 5` to reduce concurrent requests
- Cache data sources when possible

## Documentation Links

- **GitHub Provider**: https://www.pulumi.com/registry/packages/github/
- **API Reference**: https://www.pulumi.com/registry/packages/github/api-docs/
- **Examples**: https://github.com/pulumi/examples/tree/master/github-*
