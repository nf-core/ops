![GitHub Stats](https://img.shields.io/endpoint?url=https%3A%2F%2Fhealthchecks.io%2Fb%2F2%2Fd2febac8-1214-4c89-aa9c-a3f2c77b3995.shields)
![Twitter Stats](https://img.shields.io/endpoint?url=https%3A%2F%2Fhealthchecks.io%2Fb%2F2%2F5fd77e2f-16ea-4514-bd06-a49e710aab37.shields)

## Notes

https://steampipe.io/docs/integrations/gitpod
https://steampipe.io/docs/integrations/github_actions/installing_steampipe

https://hub.steampipe.io/plugins/turbot/github

## Plans

Okay so first we're going to go from Steam pipe and then Steam pipe will then run these
queries that'll all get kicked off by GitHub Actions cronjob and that cron job will run a healthcheck ping at the end, and if it doesn't ping it'll hit us with a slack notification
