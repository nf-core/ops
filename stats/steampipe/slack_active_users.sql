-- Active Users
select
  date(date_first) as day,
  count(distinct user_name)
from
  slack_access_log
group by
  day;
