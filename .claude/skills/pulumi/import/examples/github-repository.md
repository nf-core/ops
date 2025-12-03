# Importing GitHub Repositories

Import existing GitHub repositories and their configurations into Pulumi.

## Scenario: Import nf-core/modules Repository Settings

Import the nf-core/modules repository and related GitHub resources created via the web interface.

### Resources to Import

1. **Repository**: `nf-core/modules`
2. **Branch Protection**: `main` branch protection rules
3. **Team Access**: Team permissions for the repository
4. **Actions Secrets**: (Note: Cannot import existing secrets - must recreate)

## Step 1: Identify Resources

### Repository Details

```bash
# Get repository info via GitHub CLI
gh repo view nf-core/modules --json name,owner,isPrivate,description

# Or via API
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/nf-core/modules
```

**Type token**: `github:index/repository:Repository`
**ID format**: `owner/repo`
**ID value**: `nf-core/modules`

### Branch Protection

```bash
# List protected branches
gh api repos/nf-core/modules/branches/main/protection

# Get protection rules
gh api repos/nf-core/modules/branches/main/protection \
  --jq '.required_pull_request_reviews'
```

**Type token**: `github:index/branchProtection:BranchProtection`
**ID format**: `repository:pattern`
**ID value**: `nf-core/modules:main`

### Team Access

```bash
# List teams with access
gh api repos/nf-core/modules/teams

# Get team ID
gh api orgs/nf-core/teams/platform-team --jq '.id'
```

**Type token**: `github:index/teamRepository:TeamRepository`
**ID format**: `team-id:repository`
**ID value**: `12345:nf-core/modules`

## Step 2: Create Import JSON

Create `github-import.json`:

```json
{
  "resources": [
    {
      "type": "github:index/repository:Repository",
      "name": "modules_repo",
      "id": "nf-core/modules"
    },
    {
      "type": "github:index/branchProtection:BranchProtection",
      "name": "main_protection",
      "id": "nf-core/modules:main"
    },
    {
      "type": "github:index/teamRepository:TeamRepository",
      "name": "platform_team_access",
      "id": "12345:nf-core/modules"
    }
  ]
}
```

## Step 3: Configure GitHub Provider

Ensure GitHub provider is configured:

```python
# In __main__.py or as environment variable
import pulumi_github as github

# Provider uses GITHUB_TOKEN from environment
# Or configure explicitly:
provider = github.Provider(
    "github",
    token=github_token,
    owner="nf-core",
)
```

## Step 4: Execute Import

```bash
cd ~/src/nf-core/ops/pulumi/github-infrastructure

# Ensure GitHub token is set
echo $GITHUB_TOKEN  # Should show token

# Import resources
uv run pulumi import -f github-import.json -o imported-github.py -y
```

## Step 5: Review Generated Code

Example in `imported-github.py`:

```python
import pulumi
import pulumi_github as github

# Repository
modules_repo = github.Repository(
    "modules_repo",
    name="modules",
    description="Repository of modules for use with the nf-core pipeline framework",
    visibility="public",
    has_issues=True,
    has_projects=True,
    has_wiki=False,
    has_discussions=True,
    allow_merge_commit=True,
    allow_squash_merge=True,
    allow_rebase_merge=False,
    delete_branch_on_merge=True,
    vulnerability_alerts=True,
    topics=["nextflow", "nf-core", "bioinformatics"],
)

# Branch Protection
main_protection = github.BranchProtection(
    "main_protection",
    repository_id=modules_repo.node_id,
    pattern="main",
    required_pull_request_reviews=github.BranchProtectionRequiredPullRequestReviewsArgs(
        dismiss_stale_reviews=True,
        require_code_owner_reviews=True,
        required_approving_review_count=2,
    ),
    enforce_admins=True,
    require_signed_commits=False,
    required_status_checks=github.BranchProtectionRequiredStatusChecksArgs(
        strict=True,
        contexts=["ci/test", "ci/lint"],
    ),
)

# Team Access
platform_team_access = github.TeamRepository(
    "platform_team_access",
    team_id="12345",
    repository=modules_repo.name,
    permission="push",  # pull, triage, push, maintain, admin
)
```

## Step 6: Add to Program

Add to your Pulumi program with documentation:

```python
"""GitHub Infrastructure for nf-core/modules

Imported Resources:
- nf-core/modules repository
  Imported: 2025-01-02
  Originally created via GitHub web interface
"""

import pulumi
import pulumi_github as github

# === IMPORTED GITHUB RESOURCES ===

# Main repository (imported)
modules_repo = github.Repository(
    "modules_repo",
    name="modules",
    description="Repository of modules for use with the nf-core pipeline framework",
    visibility="public",
    has_issues=True,
    has_projects=True,
    has_wiki=False,
    has_discussions=True,
    allow_merge_commit=True,
    allow_squash_merge=True,
    allow_rebase_merge=False,
    delete_branch_on_merge=True,
    vulnerability_alerts=True,
    topics=["nextflow", "nf-core", "bioinformatics"],
    homepage_url="https://nf-co.re/modules",
    opts=pulumi.ResourceOptions(protect=True)  # Critical repository
)

# Branch protection (imported)
main_protection = github.BranchProtection(
    "main_protection",
    repository_id=modules_repo.node_id,
    pattern="main",
    required_pull_request_reviews=github.BranchProtectionRequiredPullRequestReviewsArgs(
        dismiss_stale_reviews=True,
        require_code_owner_reviews=True,
        required_approving_review_count=2,
    ),
    enforce_admins=True,
    required_status_checks=github.BranchProtectionRequiredStatusChecksArgs(
        strict=True,
        contexts=["ci/test", "ci/lint"],
    ),
)

# === NEW GITHUB RESOURCES ===

# New Actions secrets (existing secrets cannot be imported)
github.ActionsSecret(
    "co2_aws_key",
    repository=modules_repo.name,
    secret_name="CO2_REPORTS_AWS_ACCESS_KEY_ID",
    plaintext_value=pulumi.Output.secret(aws_access_key_id),
)

github.ActionsSecret(
    "co2_aws_secret",
    repository=modules_repo.name,
    secret_name="CO2_REPORTS_AWS_SECRET_ACCESS_KEY",
    plaintext_value=pulumi.Output.secret(aws_secret_access_key),
)

# Export outputs
pulumi.export("repository_url", modules_repo.html_url)
pulumi.export("repository_clone_url", modules_repo.ssh_clone_url)
```

## Step 7: Verify Import

```bash
# Preview - should show no changes to imported resources
uv run pulumi preview

# Check repository still accessible
gh repo view nf-core/modules
```

## Important Notes

### Cannot Import Actions Secrets

**GitHub Actions secrets cannot be imported** because they are write-only in GitHub's API.

**Options:**

1. **Recreate secrets** with Pulumi
2. **Leave existing secrets** unmanaged (manual management)
3. **Use placeholder values** and update manually

### Recreating Secrets

```python
# Create new secrets (will overwrite existing)
github.ActionsSecret(
    "secret_name",
    repository=repo.name,
    secret_name="EXISTING_SECRET",
    plaintext_value=pulumi.Output.secret(new_value),
)
```

### Repository Node ID

Branch protection requires repository's `node_id`, not `name`:

```python
# Correct
branch_protection = github.BranchProtection(
    "protection",
    repository_id=repo.node_id,  # Use node_id
    pattern="main",
)

# Incorrect
branch_protection = github.BranchProtection(
    "protection",
    repository_id=repo.name,  # Wrong - will fail
    pattern="main",
)
```

## Advanced: Import Multiple Repositories

### Discover All Organization Repositories

```bash
# List all org repos
gh repo list nf-core --limit 100 --json name,owner

# Generate import JSON
gh repo list nf-core --json name,owner --jq \
  '[.[] | {type: "github:index/repository:Repository", name: (.name | gsub("-"; "_")), id: (.owner.login + "/" + .name)}]' \
  > repos-import.json
```

### Bulk Import

```bash
# Import all repositories
uv run pulumi import -f repos-import.json -o imported-repos.py -y
```

## Common Issues

### Issue: Repository Not Found

**Problem:**

```
error: repository 'nf-core/modules' not found
```

**Solutions:**

1. Verify token has access to repository
2. Check organization name is correct
3. Verify repository exists: `gh repo view nf-core/modules`

### Issue: Branch Protection Import Fails

**Problem:**

```
error: branch protection not found for 'nf-core/modules:main'
```

**Solutions:**

1. Verify branch protection exists on that branch
2. Check branch name is correct (case-sensitive)
3. Ensure token has admin access to repository

### Issue: Team ID Not Found

**Problem:**

```
error: team repository access not found with id '12345:nf-core/modules'
```

**Solutions:**

1. Verify team has access to repository:

```bash
gh api repos/nf-core/modules/teams
```

2. Get correct team ID:

```bash
gh api orgs/nf-core/teams/platform-team --jq '.id'
```

3. Use correct format: `team-id:owner/repo`

## Best Practices

1. **Protect repositories**: `protect=True` on critical repos
2. **Import branch protection**: Ensure protection rules are managed
3. **Recreate secrets**: Import workflow, recreate secrets
4. **Document permissions**: Comment why teams have access
5. **Test webhooks**: Verify integrations still work
6. **Audit access**: Review team permissions after import

## Related Examples

- [AWS S3 Bucket Import](aws-s3-bucket.md) - Import S3 resources
- [AWS IAM Role Import](aws-iam-role.md) - Import IAM resources
