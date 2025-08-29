# Missing Workspace Participant Management Resources

## Summary

The Seqera Terraform provider is missing resources for managing workspace participants, which is needed for programmatically adding organization members to specific workspaces with defined roles.

## Use Case

We need to add nf-core GitHub team maintainers to a Seqera Platform workspace (`AWSMegatests`) with the `MAINTAIN` role as part of our Infrastructure as Code deployment.

## Current State

The provider currently has:

- ✅ `seqera_orgs` - Organization management
- ✅ `seqera_teams` - Team management
- ✅ `seqera_workspace` - Workspace creation/management
- ❌ **Missing**: Workspace participant management

## What's Missing

Based on the SDK models in the provider, the API endpoints exist but no Terraform resources are exposed:

### SDK Models Present (but not exposed as resources):

- `AddParticipantRequest`
- `AddParticipantResponse`
- `UpdateParticipantRoleRequest`
- Operations: `createworkspaceparticipant`, `updateworkspaceparticipantrole`, `deleteworkspaceparticipant`

### Needed Resources:

1. **`seqera_workspace_participant`** - Add/remove participants from workspaces
2. **`seqera_workspace_participant_role`** - Manage participant roles within workspaces

## Expected Terraform Configuration

```hcl
resource "seqera_workspace_participant" "maintainer" {
  org_id       = data.seqera_orgs.nf_core.org_id
  workspace_id = seqera_workspace.awsmegatests.id

  # One of these identification methods:
  user_name_or_email = "maintainer@example.com"
  # OR
  member_id = data.seqera_org_member.maintainer.member_id
  # OR
  team_id = data.seqera_teams.maintainers.team_id

  role = "MAINTAIN"  # OWNER, ADMIN, MAINTAIN, LAUNCH, VIEW
}
```

## API Endpoints Available

Based on the SDK, these endpoints are already implemented:

- `PUT /orgs/{orgId}/workspaces/{workspaceId}/participants/add`
- `PUT /orgs/{orgId}/workspaces/{workspaceId}/participants/{participantId}/role`
- `DELETE /orgs/{orgId}/workspaces/{workspaceId}/participants/{participantId}`

## Workaround Currently Using

We're currently working around this by calling the API directly:

```json
PUT /orgs/252464779077610/workspaces/59994744926013/participants/add
{
  "userNameOrEmail": "maintainer@example.com"
}
```

Then separately updating the role:

```json
PUT /orgs/252464779077610/workspaces/59994744926013/participants/{participantId}/role
{
  "role": "MAINTAIN"
}
```

## Environment

- Terraform Provider Version: Latest
- Seqera Platform: Cloud (api.cloud.seqera.io)
- Organization: nf-core
- Workspace: AWSMegatests

## Additional Context

This would enable full Infrastructure as Code management for Seqera Platform workspaces, allowing automated addition of team members with appropriate permissions as part of CI/CD pipelines.
