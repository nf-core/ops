select
  timestamp,
  count,
  uniques
from
  github_traffic_view_daily
where
  repository_full_name = 'nf-core/methylseq'
order by
  timestamp;
