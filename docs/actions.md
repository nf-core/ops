# GitHub Action

> We know we saturate our Github Action runners at every opportunity, we need to be more frugal with spinning up a new machine. Each new workflow requires a whole new runner, which needs to hit the APIs more times, which uses quota, money etc. By putting it in the same workflow, it can share variables, secrets, input triggers, etc. which means fewer things to maintain and go wrong. Generally, people create a new workflow when they want to create a new job.

> This is a single step workflow, which does a related thing to the test workflow (lint). My rule of thumb is if it uses the same trigger they should be in the same workflow. We could even put this in the same job as the linting to make this more efficient.

> It's only 608 lines because it duplicates all code across pytest and nf-test and it has 1 million exceptions for conda in both. Once you remove that it's only ~230 lines which is pretty low for a monorepo like this.

[Context](https://github.com/nf-core/modules/pull/4545#issuecomment-1845027257) - @adamrtalbot
