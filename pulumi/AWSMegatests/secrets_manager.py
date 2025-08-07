"""1Password secret retrieval for AWS Megatests infrastructure"""

import pulumi
import pulumi_onepassword as onepassword


def get_secrets(onepassword_provider):
    """Retrieve all required secrets from 1Password"""

    # Get Tower access token from 1Password
    tower_access_token_item = onepassword.get_item_output(
        vault="Dev",
        title="Seqera Platform",
        opts=pulumi.InvokeOptions(provider=onepassword_provider),
    )

    # Access the TOWER_ACCESS_TOKEN field from the item sections
    def find_field_value(fields):
        for field in fields:
            if hasattr(field, "label") and field.label == "TOWER_ACCESS_TOKEN":
                return field.value
            # Fallback to check if field has different attribute names
            if hasattr(field, "id") and field.id == "TOWER_ACCESS_TOKEN":
                return field.value
        return None

    tower_access_token = tower_access_token_item.sections[0].fields.apply(
        find_field_value
    )

    # Get workspace ID from 1Password (using static value for now)
    # TODO: Extract from 1Password custom field once we can access it reliably
    tower_workspace_id = "59994744926013"

    # Get GitHub token from 1Password
    github_token_item = onepassword.get_item_output(
        vault="Dev",
        title="GitHub nf-core PA Token Pulumi",
        opts=pulumi.InvokeOptions(provider=onepassword_provider),
    )
    github_token = github_token_item.credential

    # Get AWS credentials from 1Password
    aws_credentials_item = onepassword.get_item_output(
        vault="Dev",
        title="AWS megatests",
        opts=pulumi.InvokeOptions(provider=onepassword_provider),
    )

    return {
        "tower_access_token": tower_access_token,
        "tower_workspace_id": tower_workspace_id,
        "github_token": github_token,
        "aws_access_key_id": aws_credentials_item.username,
        "aws_secret_access_key": aws_credentials_item.password,
    }
