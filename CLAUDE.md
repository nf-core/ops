## Nextflow Best Practices

- Do NOT embed the configuration in nextflowConfig instead of using the snapshots field in seqerakit
- Please don't hard code the values that defeats the purpose of IaC

## Git Best Practices

- When pre-commit fails, don't try to amend the commit, because the commit didn't get made
