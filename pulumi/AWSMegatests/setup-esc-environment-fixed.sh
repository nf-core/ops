#!/bin/bash

# Setup ESC Environment for AWSMegatestsProd
echo "Setting up ESC environment nf-core/AWSMegatestsProd/aws..."

# Clear existing environment first
echo "Clearing existing environment..."
esc env rm nf-core/AWSMegatestsProd/aws --yes || true
esc env init nf-core/AWSMegatestsProd/aws

# 1. Create the base structure first
echo "Setting up base values structure..."
esc env set nf-core/AWSMegatestsProd/aws values '{}'

# 2. AWS OIDC Configuration
echo "Setting up AWS OIDC login..."
esc env set nf-core/AWSMegatestsProd/aws values.aws '{}'
esc env set nf-core/AWSMegatestsProd/aws values.aws.login '{}'
esc env set nf-core/AWSMegatestsProd/aws 'values.aws.login.fn::open::aws-login' '{}'
esc env set nf-core/AWSMegatestsProd/aws 'values.aws.login.fn::open::aws-login.oidc' '{}'
esc env set nf-core/AWSMegatestsProd/aws 'values.aws.login.fn::open::aws-login.oidc.duration' "1h"
esc env set nf-core/AWSMegatestsProd/aws 'values.aws.login.fn::open::aws-login.oidc.roleArn' "arn:aws:iam::728131696474:role/oidcProviderRole"
esc env set nf-core/AWSMegatestsProd/aws 'values.aws.login.fn::open::aws-login.oidc.sessionName' "pulumi-environments-session"

# 3. 1Password Configuration
echo "Setting up 1Password integration..."
esc env set nf-core/AWSMegatestsProd/aws values.1password '{}'
esc env set nf-core/AWSMegatestsProd/aws values.1password.secrets '{}'
esc env set nf-core/AWSMegatestsProd/aws 'values.1password.secrets.fn::open::1password-secrets' '{}'
esc env set nf-core/AWSMegatestsProd/aws 'values.1password.secrets.fn::open::1password-secrets.login' '{}'
esc env set nf-core/AWSMegatestsProd/aws 'values.1password.secrets.fn::open::1password-secrets.login.serviceAccountToken' '{}'
esc env set nf-core/AWSMegatestsProd/aws 'values.1password.secrets.fn::open::1password-secrets.login.serviceAccountToken.fn::secret' '{}'
esc env set nf-core/AWSMegatestsProd/aws 'values.1password.secrets.fn::open::1password-secrets.login.serviceAccountToken.fn::secret.ciphertext' --secret "ZXNjeAAAAAEAAAIAawb3Dkfc01LRAD/Jkg1ngTvt/0Z3SZfUTIJEtMPVJcHzmi4SCdCQ88GDK0nPKpJzrKNdJicFgxnTu6pfHXb1tyoVgCTFG5CmWEx5unBndnjj6LFxAfMQLlIJeWjsYBBMzlhT14PNhCXw+YCSmBwGnLcbT6gReCJFTmuL05QrT0/vM1/O+nXsn24qCkIxN+CZo1+nECfGRQL3mon0ZBVGAvMMdyq9n7d5sS+VBrXCBQD7nv/dd6pZd9E7E5loAbd3zp1DBtzOEn6xNQr+v+TY72fs/+FZ2toFinV8dpA3hOd2nISRqFXGISWHsTH7BC/IiIq5gZHScpK8YDTGVdu96UlUdPblnkUaaXjy31iQyfcU84kvtOekLuPr/sgMkCIZ5DxGi3EvL0Yp6s1vTT/m9OJ5cnUn1mKjK/douesLUb0cqUhl+TuCDtdd5/kYq9E8rtZXjG495fqYcjGVEyjiQeKI71ObVkepEmbsZUMu8B8mdhWaDiz8QAPIVfkuagxIJkDhRNpofUdxnlw9H34fvrZ5i6Gri6KX7dKNDovrsZaCfy00g077jS4fl16ZhdRbAjirb/8jm/N4VGjnADaJs0Mw853lNJ/vwvsMmelTklVJzCk2jK/sEXF/5MuJzugaCLmtsSvulmOwmIIvVp/tZSmRQ4eHuaT/dSd9PNtzGp6A2r9VlXyTW+wtcxjpVr52OoaRnXTsbt8qCokLg2XTSyBxPop6aSRNrbwU4aXs4ZYOu5Mzje0/6WXr+72XHG7b8Z2feHfTQhBG8Pl/A0fYauJQ25y3B5KIejq9OAJhX8eYLJLgP1s9Nr4j+63VgjhwJPbNREQvIpHK9dQt+1AMWxGEjPLEI+K6o7e3iXf1O+wCGR+6fXL7runrZkOla/BGiRnBlfqeO/e9AsvVx2ORsjQdHRTvSUCZmRZb+uxMj87LfXS2zXREWNx7kqM8qr3yGDIT4qhcG62Ef/6Hqh/o0I+YQGcLgLNbTK5UMM2CjdXqfesIjSyZlxglMQx7k4EhPkbhWXYJcNPF1iLJINl3L4RvMfV11ew/Ta6XleY/3MxnTmMvQ3NqIw1B2u6jN9xVUm86izrJIbZpBr/Ze8xd5rHCzRv+OE+tmrlnjfyE5O6Zlqfw/MBMGKviyc2bulued87vdheunRCOfWgWQRjiKOhI4IPcS//h3+mZ2Ws/cpKPLUjDwIQnTg=="

esc env set nf-core/AWSMegatestsProd/aws 'values.1password.secrets.fn::open::1password-secrets.get' '{}'
esc env set nf-core/AWSMegatestsProd/aws 'values.1password.secrets.fn::open::1password-secrets.get.github-token' '{}'
esc env set nf-core/AWSMegatestsProd/aws 'values.1password.secrets.fn::open::1password-secrets.get.github-token.ref' "op://Dev/GitHub nf-core PA Token Pulumi/password"
esc env set nf-core/AWSMegatestsProd/aws 'values.1password.secrets.fn::open::1password-secrets.get.tower-access-token' '{}'
esc env set nf-core/AWSMegatestsProd/aws 'values.1password.secrets.fn::open::1password-secrets.get.tower-access-token.ref' "op://Dev/Seqera Platform/TOWER_ACCESS_TOKEN"

# 4. Environment Variables
echo "Setting up environment variables..."
esc env set nf-core/AWSMegatestsProd/aws environmentVariables '{}'
esc env set nf-core/AWSMegatestsProd/aws environmentVariables.AWS_ACCESS_KEY_ID '${aws.login.accessKeyId}'
esc env set nf-core/AWSMegatestsProd/aws environmentVariables.AWS_SECRET_ACCESS_KEY --secret '${aws.login.secretAccessKey}'
esc env set nf-core/AWSMegatestsProd/aws environmentVariables.AWS_SESSION_TOKEN --secret '${aws.login.sessionToken}'

esc env set nf-core/AWSMegatestsProd/aws environmentVariables.AWS_REGION "eu-west-1"
esc env set nf-core/AWSMegatestsProd/aws environmentVariables.ORGANIZATION_NAME "nf-core"
esc env set nf-core/AWSMegatestsProd/aws environmentVariables.WORKSPACE_NAME "AWSmegatests"
esc env set nf-core/AWSMegatestsProd/aws environmentVariables.AWS_WORK_DIR "s3://nf-core-awsmegatests"
esc env set nf-core/AWSMegatestsProd/aws environmentVariables.AWS_CREDENTIALS_NAME "tower-awstest"
esc env set nf-core/AWSMegatestsProd/aws environmentVariables.AWS_COMPUTE_ENV_ALLOWED_BUCKETS "s3://ngi-igenomes,s3://annotation-cache"

esc env set nf-core/AWSMegatestsProd/aws environmentVariables.GITHUB_TOKEN --secret '${1password.secrets.github-token}'
esc env set nf-core/AWSMegatestsProd/aws environmentVariables.TOWER_ACCESS_TOKEN --secret '${1password.secrets.tower-access-token}'

echo "ESC environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Update Pulumi.prod.yaml to contain:"
echo "   environment:"
echo "     - AWSMegatestsProd/aws"
echo ""
echo "2. Test with: uv run pulumi preview --stack prod"