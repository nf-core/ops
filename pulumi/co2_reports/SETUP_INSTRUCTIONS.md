# CO2 Reports Pulumi Setup Instructions

## Commands to run:

```bash
# 1. Initialize the stack
cd ~/src/nf-core/ops/pulumi/co2_reports
uv run pulumi stack init AWSMegatests

# 2. Configure the stack
uv run pulumi config set aws:region us-east-1
uv run pulumi config set github:owner nf-core

# 3. Set the 1Password service account token (get this from 1Password)
uv run pulumi config set pulumi-onepassword:service_account_token <YOUR_TOKEN> --secret

# 4. Preview the changes
uv run pulumi preview

# 5. Deploy the infrastructure
uv run pulumi up

# 6. Verify the GitHub secrets were created
# Check in GitHub: https://github.com/nf-core/modules/settings/secrets/actions
```

## What this will create:

1. S3 bucket: `nf-core-co2-reports`
2. IAM user: `nf-core-co2-reports-ci`
3. IAM policy for write access to the bucket
4. GitHub Actions secrets in nf-core/modules:
   - CO2_REPORTS_AWS_ACCESS_KEY_ID
   - CO2_REPORTS_AWS_SECRET_ACCESS_KEY
   - CO2_REPORTS_AWS_REGION

## After deployment:

Update the GitHub workflow in nf-core/modules to use the new bucket and credentials.
