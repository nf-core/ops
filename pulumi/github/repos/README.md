# Repos

Goal is to replace https://oldsite.nf-co.re/pipeline_health

This repo will be the "Actions" section at the bottom. We can then create a reporting page if we really need to see all the green checks

[Old Pipeline Health PHP code](https://github.com/nf-core/website/blob/old-site/public_html/pipeline_health.php)

[New Pipeline Health page](https://github.com/nf-core/website/blob/main/sites/pipelines/src/pages/pipeline_health.astro)

## Initial Roll-out

The new pipelines that are broken:

- demo
- testpipeline

- denovotranscript
- meerpipe
- pairgenomealign
- phaseimpute
- reportho

Maybe:

- scdownstream
- scnanoseq

### Plan

#### Short-term

1. [ ] Import a pipeline that has all the right settings
2. [ ] Fix the 5 pipelines above with the correct settings from the "model" repo
3. [ ] Keep importing new pipelines until we gain confidence in it.

#### Long-term

1. Wrangle in `core_repos`
2. Roll out to all pipelines
3. Switch all repos to main
