# Cost Estimates

Estimated AWS costs for running the hackathon infrastructure.

## Instance Sizing

| Service | Instance | vCPU | RAM | Rationale |
|---------|----------|------|-----|-----------|
| WorkAdventure | t3.xlarge | 4 | 16GB | Multiple containers, game engine |
| LiveKit | c5.xlarge | 4 | 8GB | Real-time media processing needs compute |
| Coturn | t3.medium | 2 | 4GB | Relay only, low compute |
| Jitsi | t3.medium | 2 | 4GB | Small meetings, modest load |

## Daily Cost Breakdown

| Resource | Daily Cost | Notes |
|----------|------------|-------|
| WorkAdventure (t3.xlarge) | ~$4.00 | On-demand pricing |
| LiveKit (c5.xlarge) | ~$4.00 | Compute-optimized |
| Coturn (t3.medium) | ~$1.00 | |
| Jitsi (t3.medium) | ~$1.00 | |
| Elastic IPs (3) | ~$0.30 | When attached to instances |
| Application Load Balancer | ~$0.70 | Plus LCU charges |
| Route53/misc | ~$0.20 | DNS records |
| **Total** | **~$11.50/day** | |

## Event Duration Estimates

| Duration | Estimated Cost |
|----------|---------------|
| 1 day | ~$12 |
| 3 days | ~$35 |
| 1 week | ~$80 |
| 2 weeks | ~$160 |

Plus data transfer costs (usually minimal for hackathon use).

## Cost Optimization Options

### For Lower Traffic Events
- Downsize WorkAdventure to t3.large (~$3/day savings)
- Use t3.medium for LiveKit if <20 concurrent video users (~$3/day savings)

### For Higher Traffic Events
- Consider c5.2xlarge for LiveKit with 100+ concurrent video users
- Consider t3.xlarge for Jitsi if running large meetings

### Spot Instances
Not recommended for this use case - hackathon reliability is more important than cost savings from spot pricing.

## EIP Costs Note

Elastic IPs are free when attached to running instances. Costs only accrue if:
- Instance is stopped but EIP remains allocated
- Infrastructure is partially torn down

Always do a complete teardown to avoid orphaned EIP charges.

## Cost Tracking

All resources are automatically tagged for cost tracking:

| Tag | Value |
|-----|-------|
| `Project` | `nfcore-hackathon` |
| `Environment` | `hackathon` |
| `ManagedBy` | `terraform` |
| `pipeline` | `hackathon-infra` |

These tags are applied via the AWS provider's `default_tags` in `providers.tf`.

The `pipeline` tag is an existing cost allocation tag in the nf-core AWS organization, allowing costs to be tracked alongside other nf-core infrastructure.

### Using AWS Cost Explorer

1. Go to **AWS Cost Management** > **Cost Explorer**
2. Click **Group by** > **Tag** > **pipeline**
3. Filter to `hackathon-infra`
4. View costs by day, week, or custom range

Alternatively, filter by `Project` = `nfcore-hackathon` if you prefer.

### Setting Up Budget Alerts

To receive email alerts when costs exceed a threshold:

1. Go to **AWS Budgets** > **Create budget**
2. Select **Cost budget**
3. Set your budget amount (e.g., $50/month)
4. Under **Filters**, select **Tag** > **Project** > `nfcore-hackathon`
5. Configure alert thresholds (e.g., 80%, 100%)
6. Add email recipients

### Note on Tag Activation

Cost allocation tags must be activated before they appear in Cost Explorer and Budgets. Go to **Billing** > **Cost allocation tags**, select the `Project` tag, and activate it. Tags may take 24 hours to appear after activation.
