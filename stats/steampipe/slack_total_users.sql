select
  count(distinct real_name_normalized)
from
  slack_user
where
  deleted is false;
