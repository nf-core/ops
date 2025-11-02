# Pulumi Workflow Skills

Comprehensive Claude Code skills for working with Pulumi infrastructure-as-code.

## Overview

This skill collection provides expert guidance for Pulumi workflows, including deployment, stack management, project creation, and documentation access. Designed for the nf-core/ops workflow with 1Password + direnv credential management.

## Available Skills

### 1. Deploying Pulumi Infrastructure (`deploy/`)

**Triggers**: "deploy", "pulumi up", "preview", "apply changes"

Preview and deploy infrastructure changes safely:

- Standard deployment workflow
- Preview before deploy with user confirmation
- 1Password credential loading
- Error handling and troubleshooting
- Advanced deployment patterns (targeted, parallel, CI/CD)

**Files**:

- `SKILL.md` - Main deployment workflow
- `reference.md` - Advanced deployment patterns

### 2. Managing Pulumi Stacks (`stack-management/`)

**Triggers**: "stack", "switch stack", "stack output", "configuration"

Manage multiple Pulumi stacks and environments:

- List and switch stacks
- View stack outputs
- Manage stack configuration
- Multi-environment workflows
- Cross-stack references

**Files**:

- `SKILL.md` - Core stack operations
- `reference.md` - Advanced stack patterns
- `troubleshooting.md` - Common issues and solutions

### 3. Creating New Pulumi Projects (`new-project/`)

**Triggers**: "new project", "initialize pulumi", "scaffold", "start new infrastructure"

Initialize new Pulumi projects with proper structure:

- Interactive project setup
- Template files (.envrc, pyproject.toml, **main**.py)
- 1Password integration by default
- Best practices and conventions
- Component resources and testing

**Files**:

- `SKILL.md` - Project initialization workflow
- `reference.md` - Advanced project patterns
- `templates/` - Template files for new projects
  - `envrc.template` - 1Password + direnv configuration
  - `pyproject.toml` - Python dependencies
  - `main_py.template` - Main Pulumi program
  - `Pulumi.yaml` - Project configuration

### 4. Accessing Pulumi Documentation (`documentation/`)

**Triggers**: "pulumi docs", "how to", "aws pulumi", "github pulumi"

Quick access to Pulumi documentation and provider guides:

- WebSearch integration for latest docs
- Cached provider guides (AWS, GitHub, 1Password)
- Common patterns and examples
- API references

**Files**:

- `SKILL.md` - Documentation access patterns
- `reference.md` - Advanced topics
- `providers/aws.md` - AWS provider guide
- `providers/github.md` - GitHub provider guide
- `providers/onepassword.md` - 1Password provider guide

### 5. Importing Existing Infrastructure (`import/`)

**Triggers**: "import", "click-ops", "existing infrastructure", "bring under management"

Import manually created "click-ops" resources into Pulumi:

- Single resource import workflow
- Bulk import with JSON files
- Automated resource discovery
- Verification and safety checks
- Provider-specific import patterns

**Files**:

- `SKILL.md` - Core import workflows
- `reference.md` - Advanced import patterns
- `examples/aws-s3-bucket.md` - S3 import walkthrough
- `examples/aws-iam-role.md` - IAM import example
- `examples/github-repository.md` - GitHub import example
- `scripts/discover-aws-resources.py` - AWS discovery helper

## Key Features

### Progressive Disclosure

Skills follow progressive disclosure patterns:

- **SKILL.md**: Concise overview with common operations
- **reference.md**: Detailed patterns for advanced use cases
- **Supporting files**: Provider guides, templates, troubleshooting

### 1Password Integration

All skills include 1Password + direnv patterns:

- Automatic credential loading
- No secrets in code
- Consistent across all projects
- Easy credential rotation

### Safety First

Deployment skills include safety confirmations:

- Always preview before deploy
- Confirm with user for production changes
- Highlight destructive operations
- Export state before major changes

### nf-core/ops Conventions

Skills follow nf-core/ops patterns:

- S3 backend for state
- Standard project structure
- Tagging conventions
- Naming patterns

## Usage Examples

### Deploy Infrastructure

```
User: "Deploy the co2_reports infrastructure"

Claude will:
1. Load credentials from .envrc (1Password)
2. Run pulumi preview
3. Show changes and ask for confirmation
4. Deploy with pulumi up
5. Verify outputs
```

### Switch Stacks

```
User: "Switch to production stack"

Claude will:
1. List available stacks
2. Switch to production
3. Verify current stack
4. Show stack outputs
```

### Create New Project

```
User: "Create a new Pulumi project for monitoring infrastructure"

Claude will:
1. Ask for project details
2. Create directory structure
3. Generate files from templates
4. Set up dependencies
5. Initialize stack
6. Guide through first deployment
```

### Access Documentation

```
User: "How do I create an S3 bucket with encryption in Pulumi?"

Claude will:
1. Load AWS provider guide
2. Show S3 bucket example with encryption
3. Provide code snippet
4. Link to latest docs if needed
```

### Import Existing Infrastructure

```
User: "Import the nf-core-co2-reports S3 bucket into Pulumi"

Claude will:
1. Identify resource type and ID
2. Create import JSON or command
3. Execute import
4. Generate Pulumi code
5. Verify no changes in preview
6. Add protection if critical resource
```

## Project Structure

```
pulumi-workflow/
├── README.md                           # This file
├── deploy/
│   ├── SKILL.md                        # Deployment workflow
│   └── reference.md                    # Advanced patterns
├── stack-management/
│   ├── SKILL.md                        # Stack operations
│   ├── reference.md                    # Advanced stack management
│   └── troubleshooting.md              # Common issues
├── new-project/
│   ├── SKILL.md                        # Project initialization
│   ├── reference.md                    # Advanced project patterns
│   └── templates/                      # Project templates
│       ├── envrc.template
│       ├── pyproject.toml
│       ├── main_py.template
│       └── Pulumi.yaml
├── import/
│   ├── SKILL.md                        # Import workflows
│   ├── reference.md                    # Advanced import patterns
│   ├── examples/                       # Import examples
│   │   ├── aws-s3-bucket.md
│   │   ├── aws-iam-role.md
│   │   └── github-repository.md
│   └── scripts/                        # Helper scripts
│       └── discover-aws-resources.py
└── documentation/
    ├── SKILL.md                        # Documentation access
    ├── reference.md                    # Advanced topics
    └── providers/                      # Provider guides
        ├── aws.md
        ├── github.md
        └── onepassword.md
```

## Best Practices

### When Claude Uses These Skills

Claude will automatically use these skills when:

- User mentions Pulumi operations
- Infrastructure deployment is needed
- Stack management is requested
- Documentation is required

### Skill Selection

Claude chooses skills based on triggers:

- **deploy**: Preview, deployment, pulumi up
- **stack-management**: Stacks, outputs, configuration
- **new-project**: Initialize, scaffold, new project
- **import**: Import, click-ops, existing infrastructure, bring under management
- **documentation**: Docs, how-to, provider questions

### Progressive Disclosure in Action

1. **Quick Operations**: Use SKILL.md for common tasks
2. **Advanced Needs**: Reference reference.md for complex scenarios
3. **Troubleshooting**: Check troubleshooting.md for issues
4. **Provider-Specific**: Load appropriate provider guide

## Customization

### Adding Providers

To add a new provider guide:

1. Create `documentation/providers/{provider}.md`
2. Include:
   - Authentication
   - Common resources
   - Code examples
   - Best practices
   - Documentation links
3. Reference in `documentation/SKILL.md`

### Updating Templates

Templates in `new-project/templates/` can be customized:

- Modify for your organization
- Add additional providers
- Update credential patterns
- Include custom tooling

### Extending Skills

Add new skills by:

1. Creating new directory in `pulumi-workflow/`
2. Adding SKILL.md with proper frontmatter
3. Including reference files as needed
4. Following progressive disclosure patterns

## Validation

Skills validated for:

- ✓ Valid YAML frontmatter
- ✓ Required fields (name, description)
- ✓ Character limits (name ≤ 64, description ≤ 1024)
- ✓ Third-person descriptions
- ✓ Forward-slash paths
- ✓ Progressive disclosure structure

## Integration with nf-core/ops

These skills integrate with nf-core/ops patterns:

### S3 Backend

```yaml
backend:
  url: s3://nf-core-ops-pulumi-state?region=us-east-1&awssdk=v2
```

### Credential Management

```bash
# .envrc pattern
from_op AWS_ACCESS_KEY_ID="op://Dev/Pulumi-AWS-key/access key id"
from_op PULUMI_CONFIG_PASSPHRASE="op://Employee/Pulumi Passphrase/password"
```

### Project Structure

```
~/src/nf-core/ops/pulumi/
├── co2_reports/
├── megatests_infra/
└── {your_project}/
```

## Troubleshooting

### Skills Not Loading

If skills aren't being used:

1. Verify files are in `~/.claude/skills/pulumi-workflow/`
2. Check SKILL.md frontmatter is valid
3. Ensure descriptions include relevant triggers

### Credential Issues

See `stack-management/troubleshooting.md`:

- AWS credential errors
- Pulumi passphrase issues
- 1Password connectivity

### Deployment Failures

See `deploy/reference.md` for:

- Error handling patterns
- Rollback strategies
- State management

## Contributing

When updating these skills:

1. **Maintain Structure**: Keep progressive disclosure pattern
2. **Update All Files**: Modify SKILL.md and reference.md as needed
3. **Test Thoroughly**: Verify with real Pulumi operations
4. **Document Changes**: Update this README

## Version

**Version**: 1.0.0
**Created**: 2025-01-02
**Last Updated**: 2025-01-02

## Related Skills

These skills complement:

- **jj-workflow**: Version control with Jujutsu
- **nextflow-pipeline-development**: Nextflow infrastructure
- Custom nf-core/ops skills

## Resources

- **Pulumi Docs**: https://www.pulumi.com/docs/
- **nf-core/ops**: GitHub repository
- **1Password**: https://developer.1password.com/
- **direnv**: https://direnv.net/
