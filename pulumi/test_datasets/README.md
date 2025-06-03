# Test Datasets Infrastructure

This Pulumi program manages the AWS S3 infrastructure for nf-core test datasets and automatically creates GitHub Actions secrets for AWS access.

## What it creates

- **AWS S3 Bucket**: `nf-core-test-datasets` bucket with public read access
- **IAM User**: CI user with full access to the bucket
- **GitHub Actions Secrets**: Automatically creates secrets in the `nf-core/ops` repository

## Setup

1. **Configure AWS credentials**:
   ```bash
   pulumi config set aws:accessKey <your-access-key> --secret
   pulumi config set aws:secretKey <your-secret-key> --secret
   pulumi config set aws:region eu-north-1
   ```

2. **Configure 1Password**:
   ```bash
   pulumi config set pulumi-onepassword:service_account_token <your-token> --secret
   ```
   The GitHub token is automatically retrieved from 1Password at:
   `op://Dev/GitHub nf-core PA Token Pulumi/token`

3. **Install dependencies**:
   ```bash
   uv sync
   ```

4. **Deploy**:
   ```bash
   pulumi up
   ```

## GitHub Integration

This program automatically creates the following GitHub Actions secrets in the `nf-core/ops` repository:

- `AWS_ACCESS_KEY_ID`: Access key for the CI user
- `AWS_SECRET_ACCESS_KEY`: Secret key for the CI user  
- `AWS_REGION`: Set to `eu-north-1`

This replaces the need for the separate `add_github_secrets.py` script.

## Usage in GitHub Actions

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: ${{ secrets.AWS_REGION }}
```
