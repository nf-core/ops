## Notes

https://steampipe.io/docs/integrations/gitpod
https://steampipe.io/docs/integrations/github_actions/installing_steampipe

https://hub.steampipe.io/plugins/turbot/github

## Plans

Okay so first we're going to go from Steam pipe and then Steam pipe will then run these
queries that'll all get kicked off by GitHub Actions cronjob and that cron job will run a healthcheck ping at the end, and if it doesn't ping it'll hit us with a slack notification
