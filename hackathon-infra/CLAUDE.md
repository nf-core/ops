# AI Agent Guidelines for Hackathon Terraform

Instructions for AI agents working on this Terraform infrastructure project.

## Project Overview

This repository deploys the nf-core hackathon virtual event infrastructure:
- **WorkAdventure** - Virtual office platform (app.hackathon.nf-co.re)
- **LiveKit** - WebRTC media server for proximity audio/video
- **Coturn** - TURN server for NAT traversal
- **Jitsi** - Video conferencing for meeting rooms

## Skills

Skills provide step-by-step procedures for common tasks. They load automatically based on user intent, or explicitly via `/deploy`, `/teardown`, `/debug`, `/maps`.

| Skill | When to Use |
|-------|-------------|
| `deploy` | Setting up for a new event, first-time deployment, recovering from destruction |
| `teardown` | Event is over, cleanup needed, starting fresh |
| `debug` | Services unhealthy, users report problems, OAuth/video/maps not working |
| `maps` | Working with map files, syncing changes, setting up interactive zones |

---

## CRITICAL: Terraform Safety Rules

### NEVER Do Without Explicit User Confirmation

| Operation | Risk |
|-----------|------|
| `terraform force-unlock` | Corrupts state if another process is running |
| `terraform destroy -target=X` | Ignores dependencies, causes cascading failures |
| `terraform state rm/mv` | Desyncs state from reality |
| `terraform apply -replace=X` | Forces recreation, causes downtime |
| `terraform apply -auto-approve` | Skips review |
| `terraform destroy -auto-approve` | Skips confirmation |

**Why targeted destroys are dangerous:** This project uses `depends_on`. Destroying one module (e.g., Jitsi) can trigger recreation of dependent modules (e.g., WorkAdventure).

**Incident (January 2026):** A targeted destroy on Jitsi inadvertently triggered WorkAdventure recreation due to `depends_on` relationships and user_data hash changes. This required complete manual AWS cleanup.

### Safe Operations (No Confirmation Needed)

```bash
terraform init       # Initialize providers
terraform plan       # Preview changes (read-only)
terraform fmt        # Format code
terraform validate   # Check syntax
terraform state list # List resources (read-only)
terraform output     # Show outputs (read-only)
```

### Operations Requiring Confirmation

Always show plan output and ask before:
```bash
terraform apply      # "Proceed with these changes?"
terraform destroy    # "This will DESTROY all infrastructure. Proceed?"
```

---

## AWS Account Context

The nf-core AWS account contains other infrastructure. **Only manage `nfcore-hackathon-*` resources.**

### Do NOT Touch
- `runs-on--*` - CI runner instances
- `vpc-multi-runner-*` - EIPs for CI runners
- Any resource without `nfcore-hackathon` prefix

### Resource Limits
- **EIP quota:** 8 total, this project needs 3
- Check: `aws ec2 describe-addresses --profile nf-core --region eu-west-1`

---

## Key Facts

### Service Dependencies
```
WorkAdventure ──depends_on──▶ LiveKit, Coturn, Jitsi
```
Changes to dependencies can trigger WorkAdventure recreation.

### Maps Are Git-Tracked
The `maps/` folder is the source of truth. Maps are served locally from a cloned copy of this repo on the EC2 instance. Always ensure maps are committed before teardown.

### Service Startup Time
Services need **5-15 minutes** after deployment to fully initialize. Don't panic if health checks fail immediately.

---

## Communication Guidelines

1. **Explain before acting** - Describe what you're about to do
2. **Show terraform plan output** - Let user review changes
3. **Highlight destroys** - Call attention to resources being deleted
4. **Wait for approval** - Never proceed with destructive ops without explicit "yes"
5. **Validate each step** - Check success before proceeding to next step

### State Lock Handling

If Terraform reports state is locked:
```
The Terraform state is locked. Options:
1. Wait 15 minutes for auto-expiry
2. Force-unlock (DANGEROUS - requires explicit approval)

The lock was created by [user] at [time]. What would you like to do?
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Validate environment | `./scripts/validate-env.sh` |
| Check health | `./scripts/status.sh` |
| SSH to instance | `./scripts/ssh.sh <wa\|lk\|turn\|jitsi>` |
| Sync maps | `./scripts/sync-maps.sh` |
| Bootstrap backend | `./scripts/bootstrap.sh` |
