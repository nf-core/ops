# Pulumi

nf-core specific docs, links and guides.

## Quick Start

### Repo structure

This repo is a "Monorepo", basically a bunch of smaller projects inside of one bigger project.

```console
tree -L 1 pulumi
pulumi
├── AWSMegatests
├── github
├── repo-backups
├── sentieon-license-server
└── test-datasets
```

Each of these are their own projects.

### Install Pulumi

[Here's the official guide](https://www.pulumi.com/docs/clouds/aws/get-started/)

### Working with this repo

<!-- TODO Need someone fresh to run through this so we can see where the pain points are-->

1. Open up the project you want to make a change to
2. Make the change (Probably in `__main.py__`)
3. If you have a Pulumi cloud account in the nf-core org `pulumi preview` and `pulumi up` should work locally
4. Create a branch in the repo and make a PR, and a preview of the deployment should get ran.

## Terminology

Pulumi is pretty heavy on the terms and it was kinda confusing. A hierarchy kinda helps

```
Projects
├── Stacks
├──── Deployments
├──── Resources
Environments
```

### Projects

Each directory in `pulumi` is a project.

#### Stacks

Each project can have multiple stacks. For example, `dev`, `prod`, `test`.

Official quote:

> What are projects and stacks? Pulumi projects and stacks let you organize Pulumi code. Consider a Pulumi project to be analogous to a GitHub repo—a single place for code—and a stack to be an instance of that code with a separate configuration. For instance, project foo may have multiple stacks for different deployment environments (dev, test, or prod), or perhaps for different cloud configurations (geographic region for example). See Organizing Projects and Stacks for some best practices on organizing your Pulumi projects and stacks.

https://www.pulumi.com/docs/using-pulumi/organizing-projects-stacks/

##### Deployments

Everytime you push to main in this repo a new deployment of the stack goes out.

##### Resources

These are individual pieces of infrastructure. An EC2 instance, a VPC, a GitHub repo, a GitHub team are some examples.

### Environments

This is Pulumi's hosted Secrete management. I'm thinking of these like, well "Environments". The nf-core AWS, the nf-core Azure, nf-core GCP, nf-core GitHub org, the nf-core-tf GitHub org.
