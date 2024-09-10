select
  timestamp,
  count,
  uniques
from
  github_traffic_view_weekly
where
  repository_full_name = 'nf-core/methylseq'
order by
  timestamp;
