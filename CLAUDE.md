## Hackathon Infrastructure (`hackathon-infra/`)

Terraform-based infra for nf-core hackathon virtual events: WorkAdventure, LiveKit, Coturn, Jitsi on AWS eu-west-1.

### Terraform Safety

- All terraform commands from `hackathon-infra/terraform/environments/hackathon/`
- Safe without confirmation: `init`, `plan`, `fmt`, `validate`, `state list`, `output`
- **NEVER** without explicit user confirmation: `force-unlock`, `destroy -target`, `state rm/mv`, `apply -replace`, `*-auto-approve`
- Targeted destroys dangerous due to `depends_on` chains (WA depends on LK, Coturn, Jitsi)

### AWS Scope

- Only manage `nfcore-hackathon-*` resources
- Do NOT touch `runs-on--*` or `vpc-multi-runner-*` (CI infra)
- EIP quota: 8 total, hackathon needs 3

### Maps

Git-tracked in `hackathon-infra/maps/`. Source of truth. Served from cloned repo on EC2. Always commit before teardown.

---

## Nextflow Best Practices

- Do NOT embed the configuration in nextflowConfig instead of using the snapshots field in seqerakit
- Please don't hard code the values that defeats the purpose of IaC

## Git Best Practices

- When pre-commit fails, don't try to amend the commit, because the commit didn't get made

- Optimized Command for LLM Diagnosis

  uv run pulumi up --non-interactive --verbose 2 --continue-on-error --diff --yes

  This command provides:
  - --non-interactive - No interactive prompts (LLM-friendly)
  - --verbose 2 - Detailed logging for diagnosis
  - --continue-on-error - Shows all errors, doesn't stop on first failure
  - --diff - Rich diff display for changes
  - --yes - Auto-approves (when needed)
