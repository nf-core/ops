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
| S3/Route53/misc | ~$0.50 | Minimal storage |
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
