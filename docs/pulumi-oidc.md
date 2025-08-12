# Pulumi infrastructure architecture for nf-core/ops

Based on comprehensive research of the nf-core/ops repository and Pulumi best practices, this report provides clear architectural recommendations to make the infrastructure accessible and easy for the infrastructure team to contribute to, prioritizing simplicity and practical solutions.

## Current state: nf-core's infrastructure landscape

The nf-core organization operates at significant scale with **66+ bioinformatics pipelines** serving a global community. Their current infrastructure relies heavily on Terraform and AWS CloudFormation, using AWS for compute (Batch, Lambda, EC2), storage (S3), and running 60+ concurrent GitHub Actions runners with automatic scaling. The organization follows sophisticated automation patterns through GitHub Actions but hasn't yet adopted Pulumi, presenting an opportunity for modernization.

## Recommended architecture: progressive adoption with OIDC

### Phase 1: Foundation with GitHub Actions and OIDC

The most impactful first step is implementing **OpenID Connect (OIDC) authentication** between GitHub Actions, Pulumi Cloud, and AWS. This eliminates static credentials entirely, using short-lived tokens that expire automatically. Here's the implementation path:

**AWS OIDC Provider Setup:**
Create an OIDC provider in AWS that trusts GitHub Actions tokens. The trust policy should be specifically scoped to the nf-core/ops repository:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:nf-core/ops:*"
        }
      }
    }
  ]
}
```

**GitHub Actions Workflow Configuration:**

```yaml
name: Infrastructure Deployment
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

permissions:
  id-token: write
  contents: read

jobs:
  preview:
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: pulumi/auth-actions@v1
        with:
          organization: nf-core
          requested-token-type: urn:pulumi:token-type:access_token:organization

      - uses: pulumi/actions@v6
        with:
          command: preview
          stack-name: nf-core/infrastructure/dev
          comment-on-pr: true
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

This setup provides automatic preview comments on pull requests, showing exactly what infrastructure changes will occur, making reviews straightforward and safe.

### Phase 2: Pulumi ESC for configuration management

Pulumi ESC (Environments, Secrets, and Configuration) serves as the central hub for managing configuration across environments. Rather than storing secrets in multiple places, ESC provides a single source of truth with hierarchical configuration inheritance.

**Environment Structure:**

```yaml
# nf-core/base environment
values:
  aws:
    region: us-east-1
  organization:
    name: nf-core
    domain: nf-co.re

# nf-core/dev environment
imports:
  - nf-core/base
values:
  aws:
    login:
      fn::open::aws-login:
        oidc:
          roleArn: arn:aws:iam::123456789:role/nf-core-dev-role
          sessionName: pulumi-dev-session
  environment: development
  instance_type: t3.medium

# nf-core/prod environment
imports:
  - nf-core/base
values:
  aws:
    login:
      fn::open::aws-login:
        oidc:
          roleArn: arn:aws:iam::123456789:role/nf-core-prod-role
          sessionName: pulumi-prod-session
  environment: production
  instance_type: c5.2xlarge
```

This hierarchical approach allows teams to share common configuration while maintaining environment-specific overrides. ESC dynamically generates AWS credentials using OIDC, eliminating the need to store or rotate AWS access keys.

### Phase 3: Local development workflow

For developers to run `pulumi preview` and `pulumi up` locally, the setup should be straightforward and secure. The recommended approach uses **direnv** for automatic environment loading and **aws-vault** for secure credential management.

**Repository Structure:**

```
nf-core/ops/
├── .envrc                    # Auto-loads environment
├── .env.template             # Template for team members
├── infrastructure/
│   ├── Pulumi.yaml          # Project configuration
│   ├── Pulumi.dev.yaml      # Dev stack config
│   ├── Pulumi.prod.yaml     # Prod stack config
│   └── index.ts             # Main infrastructure code
└── scripts/
    └── setup-dev.sh         # One-time setup script
```

**Developer Setup Script (scripts/setup-dev.sh):**

```bash
#!/bin/bash
echo "Setting up nf-core infrastructure development environment..."

# Install required tools
if ! command -v pulumi &> /dev/null; then
    curl -fsSL https://get.pulumi.com | sh
fi

if ! command -v direnv &> /dev/null; then
    echo "Please install direnv: brew install direnv"
    exit 1
fi

# Setup Pulumi authentication
pulumi login

# Configure AWS credentials
aws-vault add nf-core-dev
echo "AWS credentials stored securely in system keychain"

# Create .env from template
cp .env.template .env
echo "Please edit .env with your settings"

# Allow direnv
direnv allow

echo "Setup complete! You can now run:"
echo "  pulumi preview -s dev"
echo "  pulumi up -s dev"
```

**Environment Configuration (.envrc):**

```bash
# Auto-load environment variables
dotenv_if_exists

# Set default Pulumi stack
export PULUMI_STACK=${PULUMI_STACK:-dev}

# Use aws-vault for AWS credentials
if command -v aws-vault &> /dev/null; then
    export AWS_PROFILE=nf-core-dev
fi

# Load Pulumi ESC environment
eval $(esc open nf-core/dev --format shell)

echo "🧬 nf-core infrastructure environment loaded"
echo "📊 Stack: $PULUMI_STACK"
```

This setup ensures developers can start contributing immediately with minimal configuration, while maintaining security through aws-vault's encrypted credential storage.

## Authentication strategy comparison and recommendation

After analyzing multiple approaches, the recommended strategy for nf-core combines **Pulumi ESC with AWS IAM OIDC**:

| Aspect                   | Recommended Solution                     | Rationale                                      |
| ------------------------ | ---------------------------------------- | ---------------------------------------------- |
| **CI/CD Authentication** | GitHub Actions OIDC → Pulumi Cloud → AWS | Eliminates all static credentials              |
| **Secret Management**    | Pulumi ESC for orchestration             | Centralized configuration with dynamic secrets |
| **Local Development**    | aws-vault + direnv + ESC                 | Secure, automated, developer-friendly          |
| **Multi-environment**    | Stack-per-environment pattern            | Clear separation with shared base config       |
| **Cost**                 | ~$50-100/month for ESC                   | Minimal compared to infrastructure spend       |

This approach balances security (no long-lived credentials), usability (simple local setup), and scalability (supports growth to hundreds of developers).

## GitHub Actions automation patterns

### Pull request workflow with automatic preview

The workflow automatically comments on PRs with infrastructure changes, making reviews transparent:

```yaml
name: Infrastructure PR Preview
on:
  pull_request:
    paths:
      - "infrastructure/**"
      - ".github/workflows/infrastructure.yml"

jobs:
  preview:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
      pull-requests: write

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: infrastructure/package-lock.json

      - name: Install dependencies
        working-directory: infrastructure
        run: npm ci

      - uses: pulumi/auth-actions@v1
        with:
          organization: nf-core
          requested-token-type: urn:pulumi:token-type:access_token:organization

      - name: Configure AWS via ESC
        uses: pulumi/esc-action@v1
        with:
          environment: "nf-core/infrastructure-dev"

      - uses: pulumi/actions@v6
        with:
          command: preview
          stack-name: nf-core/infrastructure/dev
          work-dir: ./infrastructure
          comment-on-pr: true
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

### Production deployment with approval gates

Production deployments require manual approval through GitHub Environments:

```yaml
name: Deploy to Production
on:
  push:
    branches: [main]
    paths:
      - "infrastructure/**"

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production # Requires manual approval
    permissions:
      id-token: write
      contents: read

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: infrastructure/package-lock.json

      - name: Install dependencies
        working-directory: infrastructure
        run: npm ci

      - uses: pulumi/auth-actions@v1
        with:
          organization: nf-core
          requested-token-type: urn:pulumi:token-type:access_token:organization

      - name: Configure AWS via ESC
        uses: pulumi/esc-action@v1
        with:
          environment: "nf-core/infrastructure-prod"

      - uses: pulumi/actions@v6
        with:
          command: up
          stack-name: nf-core/infrastructure/prod
          work-dir: ./infrastructure
```

## Migration strategy from Terraform

Given nf-core's existing Terraform infrastructure, a gradual migration approach minimizes risk:

**Phase 1: Coexistence (Months 1-2)**

- Keep existing Terraform infrastructure running
- Implement new resources in Pulumi
- Set up OIDC authentication pipeline
- Train team on Pulumi basics

**Phase 2: Import Critical Resources (Months 3-4)**

- Use Pulumi's import feature for existing AWS resources
- Start with stateless resources (IAM roles, policies)
- Gradually import S3 buckets and compute resources
- Maintain Terraform for complex existing setups

**Phase 3: Full Migration (Months 5-6)**

- Convert remaining Terraform to Pulumi
- Archive Terraform configurations
- Optimize Pulumi code for maintainability

## Team onboarding and contribution guide

Create a comprehensive `CONTRIBUTING.md` for the infrastructure team:

````markdown
# Contributing to nf-core Infrastructure

## Quick Start (5 minutes)

1. Install prerequisites:
   ```bash
   brew install pulumi direnv aws-vault
   ```
````

2. Clone and setup:

   ```bash
   git clone https://github.com/nf-core/ops
   cd ops
   ./scripts/setup-dev.sh
   ```

3. Make changes and preview:
   ```bash
   cd infrastructure
   pulumi preview -s dev
   ```

## Development Workflow

1. Create feature branch
2. Make infrastructure changes
3. Run `pulumi preview` locally
4. Open PR - automated preview runs
5. Get review from team
6. Merge - automatic deployment

## Available Stacks

- `dev`: Development environment (auto-deploy)
- `staging`: Staging environment (auto-deploy)
- `prod`: Production (requires approval)

## Getting Help

- Slack: #infrastructure
- Documentation: docs/infrastructure/
- Pulumi Concepts: https://www.pulumi.com/learn/

```

## Security best practices implementation

The recommended architecture implements defense in depth:

1. **No static credentials**: OIDC tokens expire within 1 hour
2. **Least privilege access**: Environment-specific IAM roles with minimal permissions
3. **Audit trails**: All infrastructure changes logged in Pulumi Cloud and AWS CloudTrail
4. **Secret rotation**: ESC handles automatic credential refresh
5. **Environment isolation**: Separate AWS accounts/roles per environment
6. **Code review requirements**: All infrastructure changes require PR approval
7. **Automated security scanning**: Policy as Code rules prevent misconfigurations

## Cost optimization

The proposed architecture adds minimal cost while providing significant value:

- **Pulumi Cloud Team**: ~$75/month (for the organization)
- **Pulumi ESC**: ~$50/month (for secrets management)
- **GitHub Actions**: Already in use, no additional cost
- **AWS costs**: Reduced through better resource management

Total additional cost: **~$125/month** - negligible compared to nf-core's AWS infrastructure spend, while providing enterprise-grade infrastructure management capabilities.

## Conclusion

This architecture provides nf-core with a modern, secure, and developer-friendly infrastructure management system. The combination of OIDC authentication, Pulumi ESC for configuration management, and GitHub Actions automation creates a robust platform that scales from individual contributors to large teams. The progressive adoption approach allows the team to migrate gradually while maintaining existing systems, minimizing risk and maximizing learning opportunities.

The key to success is starting simple - implement OIDC authentication first, then layer in ESC and local development workflows. This foundation will serve nf-core well as they continue to grow and support the global bioinformatics community.

```
