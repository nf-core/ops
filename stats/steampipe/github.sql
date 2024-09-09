select
  followers,
  teams_total_count as teams_count,
  members_with_role_total_count as member_count,
  repositories_total_count as repo_count,
  repositories_total_disk_usage as disk_usage
from
  github_organization
where
  login = 'nf-core';

-- https://hub.steampipe.io/plugins/turbot/github/tables/github_organization_collaborator
-- https://hub.steampipe.io/plugins/turbot/github/tables/github_stargazer
-- https://hub.steampipe.io/plugins/turbot/github/tables/github_traffic_view_daily
