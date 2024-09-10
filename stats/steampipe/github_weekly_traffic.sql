select
  timestamp,
  count,
  uniques
from
  github_traffic_view_weekly
where
  repository_full_name = 'turbot/steampipe'
order by
  timestamp;
