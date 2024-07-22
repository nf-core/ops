# Repos

Replaces the automatic rule enforcement from the [old Pipeline Health PHP code](https://github.com/nf-core/website/blob/old-site/public_html/pipeline_health.php),

[Main GitHub Issue](https://github.com/nf-core/ops/issues/5)
[Tracking Milestone](https://github.com/nf-core/ops/milestone/1)

## Useful Docs

- https://www.pulumi.com/registry/packages/github/api-docs/repository/
- [Old Pipeline Health PHP code](https://github.com/nf-core/website/blob/old-site/public_html/pipeline_health.php)
- [New Pipeline Health page](https://github.com/nf-core/website/blob/main/sites/pipelines/src/pages/pipeline_health.astro)

### Importing Repos

```sh
pulumi env run nf-core/github-prod -i pulumi import github:index/repository:Repository testpipeline testpipeline
```
